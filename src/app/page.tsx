'use client';

import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { toast } from 'sonner';
import {
  Hexagon, Plus, Shield, Route, Brain, Pause, Play, Gauge, Download, Settings2,
} from 'lucide-react';
import ParticleBackground from '@/components/ParticleBackground';
import ErrorBoundary from '@/components/ErrorBoundary';
import ProjectForm, { ProjectData } from '@/components/ProjectForm';
import AIAnalysisCard, { AIAnalysis } from '@/components/AIAnalysisCard';
import PipelinePhase, { PhaseData } from '@/components/PipelinePhase';
import MetricsPanel, { Metrics } from '@/components/MetricsPanel';
import ActivityLog, { LogEntry } from '@/components/ActivityLog';
import AuditPanel, { Finding } from '@/components/AuditPanel';
import Deliverables from '@/components/Deliverables';
import ThemeToggle from '@/components/ThemeToggle';
import ToolEcosystem from '@/components/ToolEcosystem';
import TrendingReposPanel from '@/components/TrendingReposPanel';
import UpgradeSweepPanel from '@/components/UpgradeSweepPanel';
import { getSettings, getEnabledIntegrations, getActiveAgents, saveSettings, type AppSettings } from '@/lib/settings';

// Lazy-load heavy components not needed on initial render
const SettingsDrawer = dynamic(() => import('@/components/SettingsDrawer'), { ssr: false });
const GitHubPanel = dynamic(() => import('@/components/GitHubPanel'), { ssr: false });
import BuildView from '@/components/BuildView';
import ModeSwitcher from '@/components/ModeSwitcher';
import { BrowseView, ResearchView, ScrapeView } from '@/components/ModeViews';
import VenturesPanel from '@/components/VenturesPanel';
import SecurityDashboard from '@/components/SecurityDashboard';
import { PHASES_DEF, type WorkspaceMode, saveBuildState, loadBuildState, clearBuildState } from '@/lib/workspace';
import EasyModeWizard from '@/components/EasyModeWizard';
import EasyBuildProgress from '@/components/EasyBuildProgress';



/* ═══════════════════════════════════════════
   APP STATES
   ═══════════════════════════════════════════ */
type AppView = 'form' | 'analyzing' | 'analysis' | 'pipeline' | 'complete';

const PREVIEW_PROJECT_STORAGE_KEY = 'agentbrowser:preview';
const GENERATED_HTML_STORAGE_KEY = 'agentbrowser:generated-html';
const GENERATED_META_STORAGE_KEY = 'agentbrowser:generated-meta';

type PreviewSnapshot = Pick<ProjectData, 'name' | 'description' | 'type' | 'audience'>;

function buildPreviewSnapshot(project: ProjectData): PreviewSnapshot {
  return {
    name: project.name,
    description: project.description,
    type: project.type,
    audience: project.audience,
  };
}

function getPreviewFingerprint(project: PreviewSnapshot): string {
  return JSON.stringify(project);
}

interface AppState {
  view: AppView;
  project: ProjectData | null;
  analysis: AIAnalysis | null;
  phases: PhaseData[];
  currentPhase: number;
  currentSubStep: number;
  metrics: Metrics;
  findings: Finding[];
  log: LogEntry[];
  confidence: number;
  pipelineRunning: boolean;
  techStack: string[];
  speed: number;
  isPaused: boolean;
}

/* ═══════════════════════════════════════════
   MAIN APP COMPONENT
   ═══════════════════════════════════════════ */
function AppContent() {
  const [showSettings, setShowSettings] = useState(false);
  const [appSettings, setAppSettings] = useState<AppSettings>(getSettings);
  const [state, setState] = useState<AppState>({
    view: 'form',
    project: null,
    analysis: null,
    phases: PHASES_DEF.map(p => ({
      id: p.id,
      name: p.name,
      icon: p.icon,
      status: 'pending' as const,
      progress: 0,
      subSteps: p.subs.map(s => ({ name: s, status: 'pending' as const })),
      estimatedTime: undefined,
    })),
    currentPhase: -1,
    currentSubStep: 0,
    metrics: { linesOfCode: 0, filesCreated: 0, testsPassing: 0, securityScore: 0 },
    findings: [],
    log: [],
    confidence: 0,
    pipelineRunning: false,
    techStack: [],
    speed: 1,
    isPaused: false,
  });

  const pipelineTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isRunningRef = useRef(false);
  const speedRef = useRef(1);
  const isPausedRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);
  const stateRef = useRef(state);
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>('build');
  const [securityStatus, setSecurityStatus] = useState<'clear' | 'warning' | 'threat'>('clear');
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Listen for settings changes (from SettingsDrawer save)
  useEffect(() => {
    const handler = () => setAppSettings(getSettings());
    window.addEventListener('ab:settings-changed', handler);
    return () => window.removeEventListener('ab:settings-changed', handler);
  }, []);

  // Keep refs in sync with state for use inside async pipeline
  useEffect(() => { speedRef.current = state.speed; }, [state.speed]);
  useEffect(() => { isPausedRef.current = state.isPaused; }, [state.isPaused]);
  useEffect(() => { stateRef.current = state; }, [state]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pipelineTimerRef.current) clearTimeout(pipelineTimerRef.current);
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      isRunningRef.current = false;
      abortRef.current?.abort();
    };
  }, []);

  // Auto-save build state (debounced 3s)
  useEffect(() => {
    if (state.view === 'pipeline' && state.pipelineRunning) {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      saveTimerRef.current = setTimeout(() => {
        saveBuildState({
          savedAt: new Date().toISOString(),
          view: state.view,
          project: state.project,
          analysis: state.analysis,
          phases: state.phases,
          currentPhase: state.currentPhase,
          currentSubStep: state.currentSubStep,
          metrics: state.metrics,
          findings: state.findings,
          log: state.log.slice(-100),
          confidence: state.confidence,
          speed: state.speed,
          isPaused: state.isPaused,
          pipelineRunning: state.pipelineRunning,
          techStack: state.techStack,
        });
        setLastSaved(new Date());
      }, 3000);
    }
    return () => { if (saveTimerRef.current) clearTimeout(saveTimerRef.current); };
  }, [state.phases, state.currentPhase, state.currentSubStep, state.confidence, state.isPaused]);

  // Restore saved build on mount
  useEffect(() => {
    const saved = loadBuildState();
    if (saved && saved.pipelineRunning) {
      toast.info('Previous build session found', {
        description: 'Click Restore to resume where you left off.',
        duration: 10000,
        action: {
          label: 'Restore',
          onClick: () => {
            setState(prev => ({
              ...prev,
              view: saved.view as AppView,
              project: saved.project,
              analysis: saved.analysis,
              phases: saved.phases,
              currentPhase: saved.currentPhase,
              currentSubStep: saved.currentSubStep,
              metrics: saved.metrics,
              findings: saved.findings,
              log: saved.log,
              confidence: saved.confidence,
              speed: saved.speed,
              isPaused: true,
              pipelineRunning: true,
              techStack: saved.techStack,
            }));
            isRunningRef.current = true;
            isPausedRef.current = true;
            speedRef.current = saved.speed;
            setLastSaved(new Date(saved.savedAt));
            runPipeline(saved.currentPhase);
          },
        },
      });
    }
  }, []);

  /* ─── Form Submit ─── */
  const handleFormSubmit = useCallback(async (data: ProjectData) => {
    // Abort any in-flight analysis request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    // Clear stale generated site cache so the new project gets a fresh build
    try {
      localStorage.removeItem(GENERATED_HTML_STORAGE_KEY);
      localStorage.removeItem(GENERATED_META_STORAGE_KEY);
      localStorage.removeItem(PREVIEW_PROJECT_STORAGE_KEY);
    } catch { /* ignore */ }

    setState(prev => ({ ...prev, view: 'analyzing', project: data }));

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectName: data.name,
          description: data.description,
          type: data.type,
          audience: data.audience,
        }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error('Analysis failed');

      const { analysis } = await res.json();
      setState(prev => ({
        ...prev,
        view: 'analysis',
        analysis,
        techStack: analysis.techStack || ['Next.js', 'TypeScript', 'Tailwind CSS', 'Prisma', 'Node.js'],
      }));
    } catch (err) {
      console.error('AI analysis error:', err);
      // Fallback analysis
      setState(prev => ({
        ...prev,
        view: 'analysis',
        analysis: {
          summary: `A ${prev.project?.type || 'web application'} named "${prev.project?.name}" that ${prev.project?.description?.slice(0, 200) || 'provides core functionality'}. The system will be built with a modern stack focusing on performance, security, and user experience.`,
          architecture: {
            frontend: 'Next.js 15 with React 19, TypeScript, and Tailwind CSS',
            backend: 'Next.js API Routes with Prisma ORM',
            database: 'PostgreSQL via Supabase with Redis caching',
            infrastructure: 'Vercel Edge with CDN and monitoring',
          },
          features: prev.project?.description
            ? ['User authentication & authorization', 'Dashboard analytics', 'Real-time notifications', 'Data management CRUD', 'Search and filtering']
            : ['Core application features', 'User management', 'Data operations', 'API endpoints'],
          risks: [
            { name: 'Scope expansion', severity: 'medium', mitigation: 'MVP-first approach with iterative delivery' },
            { name: 'Performance under load', severity: 'low', mitigation: 'Caching strategy and load testing' },
          ],
          estimatedComplexity: 'medium',
          suggestedTimeline: '4-6 weeks for full delivery',
          techStack: ['Next.js', 'TypeScript', 'Tailwind CSS', 'Prisma', 'Node.js'],
          keyComponents: ['Auth Module', 'Core API', 'Dashboard UI', 'Database Layer', 'Deploy Pipeline'],
        },
        techStack: ['Next.js', 'TypeScript', 'Tailwind CSS', 'Prisma', 'Node.js'],
      }));
    }
  }, []);

  /* ─── Start Build ─── */
  const handleStartBuild = useCallback(() => {
    const settings = getSettings();
    const enabledIntegrations = getEnabledIntegrations();
    const activeAgents = getActiveAgents();
    const integrationNames = enabledIntegrations.map(i => i.name);
    const agentNames = activeAgents.map(a => a.name);

    const parts = ['Autonomous build is now running'];
    if (integrationNames.length) parts.push(`Integrations: ${integrationNames.join(', ')}`);
    if (agentNames.length) parts.push(`Custom agents: ${agentNames.join(', ')}`);

    toast('Build pipeline started', { description: parts.join(' · ') });

    // Apply settings defaults
    speedRef.current = settings.pipeline.defaultSpeed;

    // Single setState call combines both view change and phase reset
    setState(prev => ({
      ...prev,
      view: 'pipeline',
      pipelineRunning: true,
      isPaused: false,
      speed: settings.pipeline.defaultSpeed,
      phases: PHASES_DEF.map(p => ({
        id: p.id,
        name: p.name,
        icon: p.icon,
        status: 'pending' as const,
        progress: 0,
        subSteps: p.subs.map(s => ({ name: s, status: 'pending' as const })),
        estimatedTime: undefined,
      })),
      currentPhase: 0,
      currentSubStep: 0,
      confidence: 0,
      findings: [],
      log: [],
      metrics: { linesOfCode: 0, filesCreated: 0, testsPassing: 0, securityScore: 0 },
    }));
    isRunningRef.current = true;
    isPausedRef.current = false;
    clearBuildState();
    runPipeline();
  }, []);

  /* ─── Pipeline Simulation Engine ─── */
  // Pauseable, speed-aware wait — polls every 50ms so pause/resume is near-instant
  const wait = (ms: number) => new Promise<void>(resolve => {
    const TICK = 50;
    let elapsed = 0;
    const tick = () => {
      if (!isRunningRef.current) { resolve(); return; }
      if (!isPausedRef.current) elapsed += TICK;
      if (elapsed >= ms / speedRef.current) { resolve(); return; }
      pipelineTimerRef.current = setTimeout(tick, TICK);
    };
    pipelineTimerRef.current = setTimeout(tick, TICK);
  });

  const addLog = useCallback((text: string, icon: string, color: string, category: LogEntry['category'], detail?: string) => {
    const now = new Date();
    const time = now.getHours().toString().padStart(2, '0') + ':' +
                 now.getMinutes().toString().padStart(2, '0') + ':' +
                 now.getSeconds().toString().padStart(2, '0');
    setState(prev => {
      const newLog = [...prev.log, {
        id: Math.random().toString(36).substring(2, 9),
        time, text, icon, color, category, detail,
      }];
      // Cap log entries to prevent unbounded growth
      return { ...prev, log: newLog.length > 500 ? newLog.slice(-500) : newLog };
    });
  }, []);

  const addFinding = useCallback((finding: Omit<Finding, 'id'>) => {
    setState(prev => ({
      ...prev,
      findings: [...prev.findings, { ...finding, id: Math.random().toString(36).substring(2, 9) }],
    }));
  }, []);

  const generateAuditFindings = useCallback((phaseIdx: number, subName: string) => {
    const phaseDef = PHASES_DEF[phaseIdx];
    const isSecondAudit = phaseDef.id === 11;

    if (subName.includes('Security')) {
      if (!isSecondAudit) {
        addFinding({ category: 'security', severity: 'high', title: 'Missing CSRF token on settings endpoint', location: 'api/routes.ts:156', fixed: false, phase: phaseDef.id });
        addFinding({ category: 'security', severity: 'medium', title: 'Rate limiting not configured on login', location: 'api/auth.ts:42', fixed: false, phase: phaseDef.id });
      } else {
        addFinding({ category: 'security', severity: 'pass', title: 'All security checks passed', location: 'Full scan', fixed: true, phase: phaseDef.id });
      }
    } else if (subName.includes('Race')) {
      if (!isSecondAudit) {
        addFinding({ category: 'raceConditions', severity: 'high', title: 'Token refresh race condition detected', location: 'auth/token.ts:47', fixed: false, phase: phaseDef.id });
      } else {
        addFinding({ category: 'raceConditions', severity: 'pass', title: 'No race conditions detected', location: 'Full scan', fixed: true, phase: phaseDef.id });
      }
    } else if (subName.includes('Type')) {
      addFinding({ category: 'typeSafety', severity: 'medium', title: '2 unsafe type casts found and fixed', location: 'utils/transform.ts:5', fixed: false, phase: phaseDef.id });
      addFinding({ category: 'typeSafety', severity: 'pass', title: 'All null checks verified', location: 'Full scan', fixed: true, phase: phaseDef.id });
    } else if (subName.includes('Static') || subName.includes('complexity')) {
      addFinding({ category: 'codeQuality', severity: 'low', title: 'Complex function simplified (complexity 18 → 7)', location: 'auth/login.ts:47', fixed: false, phase: phaseDef.id });
      addFinding({ category: 'codeQuality', severity: 'pass', title: 'No dead code detected', location: 'Full scan', fixed: true, phase: phaseDef.id });
    } else if (subName.includes('Smell') || subName.includes('duplication')) {
      addFinding({ category: 'codeQuality', severity: 'low', title: 'Duplicated validation extracted to shared utility', location: 'auth/middleware.ts:23', fixed: false, phase: phaseDef.id });
      addFinding({ category: 'codeQuality', severity: 'pass', title: 'No god classes detected', location: 'Full scan', fixed: true, phase: phaseDef.id });
    } else if (subName.includes('Memory') || subName.includes('resource')) {
      addFinding({ category: 'memorySafety', severity: 'pass', title: 'No memory leaks detected', location: 'Full scan', fixed: true, phase: phaseDef.id });
    } else if (subName.includes('Dependency') || subName.includes('CVE')) {
      if (!isSecondAudit) {
        addFinding({ category: 'dependencies', severity: 'high', title: '3 dependency CVEs found and patched', location: 'package.json', fixed: false, phase: phaseDef.id });
      } else {
        addFinding({ category: 'dependencies', severity: 'pass', title: 'All dependencies up to date', location: 'Full scan', fixed: true, phase: phaseDef.id });
      }
    } else if (subName.includes('Auto-fix') || subName.includes('fix')) {
      addFinding({ category: 'codeQuality', severity: 'pass', title: 'All fixable issues resolved automatically', location: 'Auto-fix engine', fixed: true, phase: phaseDef.id });
    } else if (subName.includes('verification') || subName.includes('Re-audit') || subName.includes('Final') || subName.includes('sign-off')) {
      addFinding({ category: 'security', severity: 'pass', title: 'Verification scan: all clear', location: 'Full scan', fixed: true, phase: phaseDef.id });
    }
  }, [addFinding]);

  const runPipeline = async (startPhase = 0) => {
    const settings = getSettings();

    for (let pi = startPhase; pi < PHASES_DEF.length; pi++) {
      if (!isRunningRef.current) return;

      const phaseDef = PHASES_DEF[pi];

      // Skip audit phases if skipAudit is enabled
      if (settings.pipeline.skipAudit && phaseDef.type === 'audit') {
        addLog(`Skipped: ${phaseDef.name} (audit gates disabled)`, 'skip-forward', 'text-amber-400', 'info');
        setState(prev => {
          const phases = [...prev.phases];
          phases[pi] = { ...phases[pi], status: 'completed', progress: 100 };
          const confidence = Math.min(100, Math.round(((pi + 1) / PHASES_DEF.length) * 100));
          return { ...prev, phases, confidence };
        });
        continue;
      }

      // Set phase to running
      setState(prev => {
        const phases = [...prev.phases];
        phases[pi] = { ...phases[pi], status: 'running', estimatedTime: `${phaseDef.subs.length * 3 + Math.floor(Math.random() * 8)}s` };
        return { ...prev, phases, currentPhase: pi, currentSubStep: 0 };
      });

      // Log enabled integrations for this phase
      const phaseIntegrations = getEnabledIntegrations(phaseDef.id);
      if (phaseIntegrations.length > 0) {
        addLog(`Integrations active: ${phaseIntegrations.map(i => i.name).join(', ')}`, 'plug', 'text-cyan-400', 'info');
      }

      // Log custom agents for this phase
      const activeAgents = getActiveAgents();
      if (activeAgents.length > 0 && [1, 6, 8].includes(phaseDef.id)) {
        addLog(`Custom agents: ${activeAgents.map(a => a.name).join(', ')}`, 'bot', 'text-purple-400', 'info');
      }

      addLog(`Starting: ${phaseDef.name}`, 'play', 'text-purple-400', 'build');

      // Simulate sub-steps
      for (let si = 0; si < phaseDef.subs.length; si++) {
        if (!isRunningRef.current) return;

        setState(prev => {
          const phases = [...prev.phases];
          const subSteps = [...phases[pi].subSteps];
          subSteps[si] = { ...subSteps[si], status: 'running' };
          phases[pi] = { ...phases[pi], subSteps, progress: Math.round(((si) / phaseDef.subs.length) * 100) };
          return { ...prev, phases, currentSubStep: si };
        });

        await wait(800 + Math.random() * 1400);

        const subName = phaseDef.subs[si];

        if (phaseDef.type === 'audit') {
          // Generate findings
          generateAuditFindings(pi, subName);

          // Auto-fix non-pass findings for this phase (if enabled)
          if (settings.pipeline.autoFix) {
            await wait(400 + Math.random() * 600);
            setState(prev => {
              const newFindings = [...prev.findings];
              let autoFixed = 0;
              for (const f of newFindings) {
                if (f.phase === phaseDef.id && f.severity !== 'pass' && !f.fixed) {
                  f.fixed = true;
                  autoFixed++;
                }
              }
              if (autoFixed > 0) {
                addLog(`Auto-fixed ${autoFixed} issue${autoFixed > 1 ? 's' : ''}`, 'wrench', 'text-orange-400', 'fix');
              }
              return { ...prev, findings: newFindings };
            });
          }
        } else {
          addLog(subName, 'check', 'text-emerald-400', 'build');
        }

        // Update metrics
        setState(prev => ({
          ...prev,
          metrics: {
            linesOfCode: prev.metrics.linesOfCode + Math.floor(Math.random() * 200) + 50,
            filesCreated: prev.metrics.filesCreated + (Math.random() > 0.5 ? 1 : 0),
            testsPassing: prev.metrics.testsPassing + (Math.random() > 0.6 ? 1 : 0),
            securityScore: Math.min(100, prev.metrics.securityScore + (phaseDef.type === 'audit' ? Math.floor(Math.random() * 15) + 5 : Math.floor(Math.random() * 3))),
          },
        }));

        // Mark sub-step as completed
        setState(prev => {
          const phases = [...prev.phases];
          const subSteps = [...phases[pi].subSteps];
          subSteps[si] = { ...subSteps[si], status: 'completed' };
          phases[pi] = { ...phases[pi], subSteps, progress: Math.round(((si + 1) / phaseDef.subs.length) * 100) };
          return { ...prev, phases, currentSubStep: si + 1 };
        });
      }

      // Phase complete
      if (phaseDef.type === 'audit') {
        // Check for any remaining critical issues
        setState(prev => {
          const criticals = prev.findings.filter(f => f.phase === phaseDef.id && f.severity === 'critical');
          if (criticals.length > 0) {
            addLog(`Audit gate: ${criticals.length} critical issue(s) — auto-fixing`, 'shield', 'text-red-400', 'audit');
            const newFindings = [...prev.findings];
            for (const f of newFindings) {
              if (f.phase === phaseDef.id && f.severity === 'critical') {
                f.fixed = true;
                f.severity = 'pass';
              }
            }
            addLog('All critical issues resolved', 'check-circle', 'text-emerald-400', 'fix');
            return { ...prev, findings: newFindings };
          } else {
            addLog(`Audit gate passed — no critical issues`, 'shield', 'text-emerald-400', 'audit');
            return prev;
          }
        });
      } else {
        addLog(`Completed: ${phaseDef.name}`, 'check-check', 'text-emerald-400', 'build');
      }

      // Mark phase as completed
      setState(prev => {
        const phases = [...prev.phases];
        phases[pi] = { ...phases[pi], status: 'completed', progress: 100 };
        const confidence = Math.min(100, Math.round(((pi + 1) / PHASES_DEF.length) * 100));
        return { ...prev, phases, confidence };
      });
    }

    // Pipeline complete — generate the real site
    addLog('Generating final site...', 'code', 'text-blue-400', 'build');
    try {
      const projectSnap = stateRef.current?.project;
      if (projectSnap) {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: projectSnap.name,
            description: projectSnap.description,
            type: projectSnap.type,
            audience: projectSnap.audience,
          }),
        });
        if (res.ok) {
          const site = await res.json() as { html: string; businessType: string };
          const previewSnapshot = buildPreviewSnapshot(projectSnap);
          try {
            localStorage.setItem(GENERATED_HTML_STORAGE_KEY, site.html);
            localStorage.setItem(PREVIEW_PROJECT_STORAGE_KEY, JSON.stringify(previewSnapshot));
            localStorage.setItem(GENERATED_META_STORAGE_KEY, getPreviewFingerprint(previewSnapshot));
          } catch { /* ignore quota */ }
          addLog(`Site generated: ${site.businessType} template applied`, 'check-check', 'text-emerald-400', 'build');
        }
      }
    } catch { /* non-critical — preview can still generate on the fly */ }

    isRunningRef.current = false;
    setState(prev => ({
      ...prev,
      pipelineRunning: false,
      isPaused: false,
      confidence: 100,
      metrics: { ...prev.metrics, securityScore: 97 },
    }));
    addLog('Project complete and delivered!', 'party-popper', 'text-purple-400', 'deploy');
    toast.success('Project Delivered!', { description: 'Your project is built, audited, and live.' });

    // Confetti celebration — dynamic import to avoid 9KB in initial bundle
    import('canvas-confetti').then(({ default: confetti }) => {
      confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 } });
      setTimeout(() => {
        confetti({ particleCount: 60, angle: 60, spread: 55, origin: { x: 0 } });
        confetti({ particleCount: 60, angle: 120, spread: 55, origin: { x: 1 } });
      }, 400);
    });

    // Switch to complete view after a delay
    await wait(1600);
    setState(prev => ({ ...prev, view: 'complete' }));
  };

  /* ─── Pause / Resume ─── */
  const handlePauseResume = useCallback(() => {
    setState(prev => ({ ...prev, isPaused: !prev.isPaused }));
  }, []);

  /* ─── Speed Control ─── */
  const handleSpeedChange = useCallback((speed: number) => {
    setState(prev => ({ ...prev, speed }));
  }, []);

  /* ─── Export Report ─── */
  const handleExportReport = useCallback(() => {
    const report = {
      exportedAt: new Date().toISOString(),
      project: state.project,
      techStack: state.techStack,
      metrics: state.metrics,
      phases: state.phases.map(p => ({
        id: p.id, name: p.name, status: p.status, progress: p.progress,
        subSteps: p.subSteps,
      })),
      auditFindings: state.findings,
      activityLog: state.log.map(e => ({ time: e.time, text: e.text, category: e.category })),
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${state.project?.name?.replace(/\s+/g, '-').toLowerCase() ?? 'report'}-build-report.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Report exported', { description: 'Build report downloaded as JSON' });
  }, [state.project, state.techStack, state.metrics, state.phases, state.findings, state.log]);

  /* ─── New Project ─── */
  const handleNewProject = useCallback(() => {
    isRunningRef.current = false;
    if (pipelineTimerRef.current) clearTimeout(pipelineTimerRef.current);
    clearBuildState();
    try {
      localStorage.removeItem(PREVIEW_PROJECT_STORAGE_KEY);
      localStorage.removeItem(GENERATED_HTML_STORAGE_KEY);
      localStorage.removeItem(GENERATED_META_STORAGE_KEY);
    } catch {
      // ignore storage errors
    }
    setState(prev => ({
      ...prev,
      view: 'form',
      project: null,
      analysis: null,
      phases: PHASES_DEF.map(p => ({
        id: p.id,
        name: p.name,
        icon: p.icon,
        status: 'pending' as const,
        progress: 0,
        subSteps: p.subs.map(s => ({ name: s, status: 'pending' as const })),
        estimatedTime: undefined,
      })),
      currentPhase: -1,
      currentSubStep: 0,
      metrics: { linesOfCode: 0, filesCreated: 0, testsPassing: 0, securityScore: 0 },
      findings: [],
      log: [],
      confidence: 0,
      pipelineRunning: false,
      techStack: [],
    }));
  }, []);

  /* ─── Manual Audit ─── */
  const handleRunAudit = useCallback(() => {
    if (state.pipelineRunning) return;
    toast.warning('Manual audit triggered', { description: 'Running full audit across all code' });
    addLog('Manual audit triggered by user', 'shield', 'text-amber-400', 'audit');

    // Simulate audit findings
    const categories = ['security', 'performance', 'typeSafety', 'codeQuality', 'raceConditions', 'memorySafety', 'dependencies'] as const;
    for (const cat of categories) {
      addFinding({
        category: cat,
        severity: 'pass',
        title: `${cat} check passed`,
        location: 'Full scan',
        fixed: true,
        phase: 0,
      });
    }

    setState(prev => ({
      ...prev,
      metrics: { ...prev.metrics, securityScore: Math.min(100, prev.metrics.securityScore + 5) },
    }));
  }, [state.pipelineRunning, addLog, addFinding]);

  /* ─── Computed values ─── */
  const auditScore = useMemo(() => state.findings.length > 0
    ? Math.round((state.findings.filter(f => f.severity === 'pass').length / state.findings.length) * 100)
    : 0, [state.findings]);

  const totalChecks = state.findings.length;
  const passedChecks = useMemo(() => state.findings.filter(f => f.severity === 'pass').length, [state.findings]);

  const isEasyMode = appSettings.mode === 'easy';

  // In easy mode, auto-start build when analysis is ready
  useEffect(() => {
    if (isEasyMode && state.view === 'analysis' && state.analysis) {
      handleStartBuild();
    }
  }, [isEasyMode, state.view, state.analysis, handleStartBuild]);

  /* ─── Easy mode: Test & Download ─── */
  const handleTestProject = useCallback(() => {
    if (!state.project) return;
    const previewSnapshot = buildPreviewSnapshot(state.project);
    try {
      localStorage.setItem(PREVIEW_PROJECT_STORAGE_KEY, JSON.stringify(previewSnapshot));
      if (localStorage.getItem(GENERATED_META_STORAGE_KEY) !== getPreviewFingerprint(previewSnapshot)) {
        localStorage.removeItem(GENERATED_HTML_STORAGE_KEY);
        localStorage.removeItem(GENERATED_META_STORAGE_KEY);
      }
    } catch {
      // ignore storage errors
    }
    window.open('/preview', '_blank', 'noopener,noreferrer');
    toast.success('Preview opened!', { description: 'Your site is launching in a new tab.' });
  }, [state.project]);

  const handleDownloadProject = useCallback(() => {
    const project = state.project;
    if (!project) {
      handleExportReport();
      return;
    }

    const previewSnapshot = buildPreviewSnapshot(project);
    const expectedFingerprint = getPreviewFingerprint(previewSnapshot);
    const html = typeof window !== 'undefined' ? localStorage.getItem(GENERATED_HTML_STORAGE_KEY) : null;
    const cachedFingerprint = typeof window !== 'undefined' ? localStorage.getItem(GENERATED_META_STORAGE_KEY) : null;

    if (html && cachedFingerprint === expectedFingerprint) {
      const blob = new Blob([html], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${project.name.replace(/\s+/g, '-').toLowerCase() || 'site'}.html`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Site downloaded!', { description: 'Open the HTML file in any browser or deploy it anywhere.' });
    } else {
      fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(previewSnapshot),
      })
        .then(async r => {
          if (!r.ok) {
            throw new Error('Generation failed');
          }
          return r.json() as Promise<{ html: string }>;
        })
        .then((data: { html: string }) => {
          try {
            localStorage.setItem(GENERATED_HTML_STORAGE_KEY, data.html);
            localStorage.setItem(GENERATED_META_STORAGE_KEY, expectedFingerprint);
          } catch {
            // ignore storage errors
          }
          const blob = new Blob([data.html], { type: 'text/html' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${project.name.replace(/\s+/g, '-').toLowerCase() || 'site'}.html`;
          a.click();
          URL.revokeObjectURL(url);
          toast.success('Site downloaded!', { description: 'Open the HTML file in any browser.' });
        })
        .catch(() => {
          handleExportReport();
        });
    }
  }, [state.project, handleExportReport]);

  /* ═══════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════ */
  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {appSettings.ui.particles && <ParticleBackground />}

      {/* ─── Top Bar ─── */}
      <header className="relative z-40 flex items-center gap-3 px-4 sm:px-6 h-14 border-b border-border/30 glass-strong flex-shrink-0">
        <div className="flex items-center gap-2">
          <Hexagon className="w-5 h-5 text-primary" />
          <span className="text-sm font-bold tracking-tight">
            Agent<span className="text-primary">Browser</span>
          </span>
        </div>

        <div className="w-px h-6 bg-border/30 mx-1 hidden sm:block" />

        {/* Project selector (hidden in easy mode during build) */}
        {!(isEasyMode && (state.view === 'pipeline' || state.view === 'complete')) && (
          <button
            onClick={handleNewProject}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border/30 bg-background/30 text-xs text-muted-foreground hover:text-foreground hover:border-primary/30 transition-all duration-200"
          >
            <Plus className="w-2.5 h-2.5" />
            <span className="hidden sm:inline truncate max-w-[160px]">
              {state.project?.name || 'New Project'}
            </span>
          </button>
        )}

        <ModeSwitcher mode={workspaceMode} onChange={setWorkspaceMode} buildRunning={state.pipelineRunning} />

        <div className="flex-1" />

        {/* Confidence Badge */}
        {state.confidence > 0 && (
          <div className={`hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold border ${
            state.confidence >= 90
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : state.confidence >= 60
              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              : 'bg-red-500/10 text-red-400 border-red-500/20'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${state.confidence >= 90 ? 'bg-emerald-400' : state.confidence >= 60 ? 'bg-amber-400' : 'bg-red-400'} animate-pulse`} />
            {state.confidence}% Complete
          </div>
        )}

        {/* Phase indicator (dev only) */}
        {!isEasyMode && state.view === 'pipeline' && state.currentPhase >= 0 && (
          <span className="hidden md:inline text-[10px] text-muted-foreground font-mono">
            Phase {state.currentPhase + 1}/{PHASES_DEF.length}
          </span>
        )}

        <div className="w-px h-6 bg-border/30 mx-1 hidden sm:block" />

        {/* Mode badge - click to toggle */}
        <button
          onClick={() => {
            const newMode = appSettings.mode === 'easy' ? 'dev' : 'easy';
            const newSettings = { ...appSettings, mode: newMode };
            setAppSettings(newSettings);
            saveSettings(newSettings);
          }}
          className={`hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider transition-all hover:scale-105 ${
            appSettings.mode === 'dev'
              ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
              : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
          }`}
          title="Click to switch between Easy and Dev mode"
        >
          {appSettings.mode}
        </button>

        <button
          onClick={() => setWorkspaceMode('security')}
          title="Security Status"
          className="p-2 rounded-xl hover:bg-white/10 transition-all"
        >
          <Shield className={`w-3.5 h-3.5 ${
            securityStatus === 'clear' ? 'text-green-400' :
            securityStatus === 'warning' ? 'text-yellow-400' :
            'text-red-400'
          }`} />
        </button>

        {!isEasyMode && (
          <button
            onClick={() => setShowSettings(true)}
            title="Settings & integrations"
            className="relative p-2 rounded-xl hover:bg-white/10 text-foreground/60 hover:text-foreground transition-all"
          >
            <Settings2 className="w-3.5 h-3.5" />
            {getEnabledIntegrations().length > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center w-3.5 h-3.5 rounded-full bg-primary text-[8px] font-bold text-primary-foreground">
                {getEnabledIntegrations().length}
              </span>
            )}
          </button>
        )}

        <ThemeToggle />

        <button
          onClick={handleNewProject}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white transition-all duration-200 hover:scale-105 active:scale-95"
          style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.5 0.18 260))' }}
        >
          <Plus className="w-2.5 h-2.5" />
          <span className="hidden sm:inline">New</span>
        </button>
      </header>

      {/* ─── Main Content ─── */}
      <main className="relative z-10 flex-1 overflow-y-auto">
        {workspaceMode === 'build' && (<>

        {/* ═══ EASY MODE BUILD FLOW ═══ */}
        {isEasyMode && (
          <>
            {/* Easy wizard (form) */}
            {state.view === 'form' && (
              <EasyModeWizard onSubmit={handleFormSubmit} />
            )}

            {/* Easy analyzing spinner */}
            {(state.view === 'analyzing' || state.view === 'analysis') && (
              <div className="min-h-full flex items-center justify-center p-4 sm:p-8">
                <div className="text-center animate-fade-in-up space-y-4">
                  <div className="relative inline-block">
                    <div className="w-20 h-20 rounded-2xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190))' }}>
                      <Brain className="w-6 h-6 text-white animate-pulse" />
                    </div>
                    <div className="absolute -inset-2 rounded-3xl border-2 border-primary/20 animate-ping opacity-30" />
                  </div>
                  <h2 className="text-xl font-bold text-foreground">Getting everything ready...</h2>
                  <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                    We&apos;re planning the best way to build what you described. This only takes a moment.
                  </p>
                  <div className="flex items-center justify-center gap-3 pt-2">
                    {[0, 1, 2].map(i => (
                      <div key={i} className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: `${i * 200}ms` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Easy build progress */}
            {(state.view === 'pipeline' || state.view === 'complete') && (
              <EasyBuildProgress
                phases={state.phases}
                currentPhase={state.currentPhase}
                confidence={state.confidence}
                isPaused={state.isPaused}
                pipelineRunning={state.pipelineRunning}
                lastSaved={lastSaved}
                projectName={state.project?.name || 'Your Project'}
                onTest={handleTestProject}
                onDownload={handleDownloadProject}
              />
            )}
          </>
        )}

        {/* ═══ DEV MODE BUILD FLOW ═══ */}
        {!isEasyMode && (
          <>
            {/* FORM VIEW */}
            {state.view === 'form' && (
              <div className="min-h-full flex flex-col items-center justify-start p-4 sm:p-8 gap-6 overflow-y-auto">
                <ProjectForm onSubmit={handleFormSubmit} isAnalyzing={false} />
                <div className="w-full max-w-2xl space-y-6">
                  <UpgradeSweepPanel />
                  <ToolEcosystem />
                  <TrendingReposPanel />
                  <GitHubPanel />
                </div>
              </div>
            )}

            {/* ANALYZING VIEW */}
            {state.view === 'analyzing' && (
              <div className="min-h-full flex items-center justify-center p-4 sm:p-8">
                <div className="text-center animate-fade-in-up">
                  <div className="relative inline-block mb-6">
                    <div className="w-20 h-20 rounded-2xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190))' }}>
                      <Brain className="w-6 h-6 text-white animate-pulse" />
                    </div>
                    <div className="absolute -inset-2 rounded-3xl border-2 border-primary/20 animate-ping opacity-30" />
                  </div>
                  <h2 className="text-xl font-bold text-foreground mb-2">AI is analyzing your project</h2>
                  <p className="text-sm text-muted-foreground max-w-md mx-auto">
                    Our AI architect is reviewing your requirements, researching best practices, and creating a comprehensive project blueprint.
                  </p>
                  <div className="mt-6 flex items-center justify-center gap-3">
                    {[0, 1, 2].map(i => (
                      <div key={i} className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: `${i * 200}ms` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ANALYSIS VIEW */}
            {state.view === 'analysis' && state.analysis && (
              <div className="min-h-full flex items-center justify-center p-4 sm:p-8">
                <AIAnalysisCard
                  analysis={state.analysis}
                  onStart={handleStartBuild}
                  isStarting={false}
                />
              </div>
            )}

            {/* PIPELINE VIEW */}
            {state.view === 'pipeline' && (
              <div className="h-full">
                <BuildView
                  project={state.project}
                  phases={state.phases}
                  currentPhase={state.currentPhase}
                  currentSubStep={state.currentSubStep}
                  isPaused={state.isPaused}
                  pipelineRunning={state.pipelineRunning}
                  confidence={state.confidence}
                  speed={state.speed}
                  metrics={state.metrics}
                  findings={state.findings}
                  log={state.log}
                  lastSaved={lastSaved}
                  onPauseResume={handlePauseResume}
                  onSpeedChange={handleSpeedChange}
                  onRunAudit={handleRunAudit}
                  onExport={handleExportReport}
                />
              </div>
            )}

            {/* COMPLETE VIEW */}
            {state.view === 'complete' && state.project && (
              <div className="max-w-5xl mx-auto p-4 sm:p-6 animate-fade-in-up">
                <Deliverables
                  projectName={state.project.name}
                  techStack={state.techStack}
                  metrics={state.metrics}
                />
                <div className="mt-6">
                  <ActivityLog entries={state.log} />
                </div>
                <div className="mt-6 flex items-center justify-center gap-3">
                  <button
                    onClick={handleExportReport}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm border border-border/30 bg-background/30 text-muted-foreground hover:text-foreground hover:border-primary/30 transition-all duration-200 hover:scale-105 active:scale-95"
                  >
                    <Download className="w-4 h-4" />
                    Export Report
                  </button>
                  <button
                    onClick={handleNewProject}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm text-white transition-all duration-300 hover:scale-105 active:scale-95"
                    style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190), oklch(0.55 0.18 160))' }}
                  >
                    <Plus className="w-4 h-4" />
                    Start New Project
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        </>)}
        {workspaceMode === 'browse' && <BrowseView />}
        {workspaceMode === 'research' && <ResearchView />}
        {workspaceMode === 'scrape' && <ScrapeView />}
        {workspaceMode === 'ventures' && <VenturesPanel />}
        {workspaceMode === 'security' && <SecurityDashboard />}
      </main>

      <SettingsDrawer open={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  );
}

/* ═══════════════════════════════════════════
   ROOT EXPORT WITH PROVIDERS
   ═══════════════════════════════════════════ */
export default function Home() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}
