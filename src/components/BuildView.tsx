'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Check, Circle, Loader2, Pause, Play, Gauge, Shield, Download,
  Save, ChevronDown, ChevronRight, Eye, EyeOff,
} from 'lucide-react';
import { AppIcon } from '@/lib/icons';
import type { PhaseData } from '@/components/PipelinePhase';
import type { Metrics } from '@/components/MetricsPanel';
import type { Finding } from '@/components/AuditPanel';
import type { LogEntry } from '@/components/ActivityLog';
import type { ProjectData } from '@/components/ProjectForm';
import MetricsPanel from '@/components/MetricsPanel';
import AuditPanel from '@/components/AuditPanel';
import ActivityLog from '@/components/ActivityLog';
import { PHASES_DEF } from '@/lib/workspace';

/* ═══════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════ */
export interface BuildViewProps {
  project: ProjectData | null;
  phases: PhaseData[];
  currentPhase: number;
  currentSubStep: number;
  isPaused: boolean;
  pipelineRunning: boolean;
  confidence: number;
  speed: number;
  metrics: Metrics;
  findings: Finding[];
  log: LogEntry[];
  lastSaved: Date | null;
  onPauseResume: () => void;
  onSpeedChange: (speed: number) => void;
  onRunAudit: () => void;
  onExport: () => void;
}

/* ═══════════════════════════════════════════
   HELPERS
   ═══════════════════════════════════════════ */
function timeSince(date: Date): string {
  const s = Math.floor((Date.now() - date.getTime()) / 1000);
  if (s < 5) return 'just now';
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

/* ═══════════════════════════════════════════
   BUILD VIEW COMPONENT
   ═══════════════════════════════════════════ */
export default function BuildView({
  project, phases, currentPhase, currentSubStep,
  isPaused, pipelineRunning, confidence, speed,
  metrics, findings, log, lastSaved,
  onPauseResume, onSpeedChange, onRunAudit, onExport,
}: BuildViewProps) {
  const activeStepRef = useRef<HTMLDivElement>(null);
  const [showLog, setShowLog] = useState(false);
  const [savedText, setSavedText] = useState('');

  // Auto-scroll to active step
  useEffect(() => {
    activeStepRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [currentPhase, currentSubStep]);

  // Update "saved X ago" text periodically
  useEffect(() => {
    if (!lastSaved) return;
    const update = () => setSavedText(timeSince(lastSaved));
    update();
    const id = setInterval(update, 5000);
    return () => clearInterval(id);
  }, [lastSaved]);

  // Computed audit values
  const auditScore = useMemo(() =>
    findings.length > 0
      ? Math.round((findings.filter(f => f.severity === 'pass').length / findings.length) * 100)
      : 0,
    [findings],
  );
  const totalChecks = findings.length;
  const passedChecks = useMemo(() => findings.filter(f => f.severity === 'pass').length, [findings]);

  return (
    <div className="flex flex-col h-full animate-fade-in-up">
      {/* ─── Header: project + progress + auto-save ─── */}
      <div className="px-4 sm:px-6 pt-4 pb-3 flex-shrink-0">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-lg sm:text-xl font-bold text-foreground truncate">{project?.name ?? 'Building...'}</h1>
            <p className="text-xs text-muted-foreground mt-0.5 max-w-lg truncate">
              {project?.description || 'Autonomous build in progress'}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {isPaused && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 border border-amber-500/20 text-amber-400 animate-pulse">
                <Pause className="w-2.5 h-2.5" /> Paused
              </span>
            )}
            {lastSaved && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <Save className="w-2.5 h-2.5" /> {savedText}
              </span>
            )}
          </div>
        </div>
        {/* Overall progress */}
        <div className="mt-3">
          <div className="flex items-center justify-between text-[10px] text-muted-foreground mb-1">
            <span>Overall progress</span>
            <span className="font-mono">{confidence}%</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-muted/30 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${confidence}%`,
                background: confidence === 100
                  ? 'linear-gradient(90deg, oklch(0.6 0.2 160), oklch(0.55 0.22 140))'
                  : 'linear-gradient(90deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190))',
              }}
            />
          </div>
        </div>
      </div>

      {/* ─── Pipeline Visualizer (horizontal flow) ─── */}
      <div className="px-4 sm:px-6 flex-shrink-0">
        <div className="flex items-center gap-0 overflow-x-auto py-3 px-1 scrollbar-thin">
          {phases.map((phase, i) => (
            <div key={phase.id} className="flex items-center flex-shrink-0">
              {/* Phase node */}
              <div className="relative flex flex-col items-center" style={{ minWidth: i === currentPhase ? 70 : 36 }}>
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold transition-all duration-500 ${
                  phase.status === 'completed'
                    ? 'bg-emerald-500/25 text-emerald-400 border border-emerald-500/40 shadow-sm shadow-emerald-500/20'
                    : phase.status === 'running'
                    ? 'bg-primary/25 text-primary border-2 border-primary/50 shadow-md shadow-primary/30 scale-110'
                    : 'bg-muted/15 text-muted-foreground/40 border border-border/20'
                }`}>
                  {phase.status === 'completed' ? <Check className="w-3 h-3" /> :
                   phase.status === 'running' ? <Loader2 className="w-3 h-3 animate-spin" /> :
                   phase.id}
                </div>
                {/* Label for active phase */}
                {i === currentPhase && (
                  <span className="mt-1 text-[8px] font-bold text-primary whitespace-nowrap leading-tight text-center max-w-[70px] truncate">
                    {phase.name.length > 12 ? phase.name.split(' ').slice(0, 2).join(' ') : phase.name}
                  </span>
                )}
                {/* Pulse ring on active */}
                {phase.status === 'running' && (
                  <div className="absolute -inset-1 rounded-full border border-primary/20 animate-ping opacity-30" />
                )}
              </div>
              {/* Connector line */}
              {i < phases.length - 1 && (
                <div className={`w-3 sm:w-5 h-0.5 flex-shrink-0 transition-all duration-500 rounded-full ${
                  phase.status === 'completed' && phases[i + 1]?.status !== 'pending'
                    ? 'bg-emerald-500/40'
                    : phase.status === 'completed'
                    ? 'bg-gradient-to-r from-emerald-500/40 to-muted/15'
                    : 'bg-muted/15'
                }`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ─── Main content: Steps + Sidebar ─── */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 px-4 sm:px-6 overflow-hidden min-h-0">
        {/* Steps checklist (scrollable) */}
        <div className="lg:col-span-2 overflow-y-auto pr-1 scrollbar-thin space-y-0.5 pb-4">
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 sticky top-0 bg-background/80 backdrop-blur-sm py-1 z-10">
            Build Steps
          </h2>
          {PHASES_DEF.map((phaseDef, pi) => {
            const phase = phases[pi];
            if (!phase) return null;
            const isActive = pi === currentPhase;
            const isCompleted = phase.status === 'completed';
            const isPending = phase.status === 'pending';

            return (
              <div key={phaseDef.id} className="mb-1">
                {/* Phase header bullet */}
                <div
                  ref={isActive ? activeStepRef : undefined}
                  className={`flex items-center gap-2 py-1.5 px-2 rounded-lg transition-all duration-300 ${
                    isActive ? 'bg-primary/8 border border-primary/20' :
                    isCompleted ? 'opacity-70' : 'opacity-40'
                  }`}
                >
                  {/* Status icon */}
                  <div className={`w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 ${
                    isCompleted ? 'bg-emerald-500/20 text-emerald-400' :
                    isActive ? 'bg-primary/20 text-primary' :
                    'bg-muted/20 text-muted-foreground/50'
                  }`}>
                    {isCompleted ? <Check className="w-3 h-3" /> :
                     isActive ? <Loader2 className="w-3 h-3 animate-spin" /> :
                     <Circle className="w-2.5 h-2.5" />}
                  </div>
                  {/* Phase name + icon */}
                  <AppIcon name={phaseDef.icon} className={`w-3 h-3 flex-shrink-0 ${
                    isCompleted ? 'text-emerald-400' : isActive ? 'text-primary' : 'text-muted-foreground/50'
                  }`} />
                  <span className={`text-xs font-semibold truncate ${
                    isCompleted ? 'text-foreground/80' : isActive ? 'text-foreground' : 'text-muted-foreground/60'
                  }`}>
                    {phaseDef.name}
                  </span>
                  {phaseDef.type === 'audit' && (
                    <Shield className="w-2.5 h-2.5 text-amber-400 flex-shrink-0 ml-auto" />
                  )}
                  {isActive && phase.progress > 0 && (
                    <span className="ml-auto text-[9px] font-mono text-primary">{phase.progress}%</span>
                  )}
                </div>

                {/* Sub-steps as indented bullets */}
                {(!isPending || isActive) && (
                  <div className="ml-4 border-l border-border/20 pl-3 space-y-0">
                    {phaseDef.subs.map((sub, si) => {
                      const subStatus = phase.subSteps[si]?.status ?? 'pending';
                      const isCurrentSub = isActive && si === currentSubStep;

                      return (
                        <div
                          key={si}
                          ref={isCurrentSub ? activeStepRef : undefined}
                          className={`flex items-start gap-2 py-1 px-2 rounded text-[11px] transition-all duration-200 ${
                            isCurrentSub ? 'bg-primary/5 text-primary font-medium' :
                            subStatus === 'completed' ? 'text-emerald-400/80' :
                            subStatus === 'running' ? 'text-primary' :
                            'text-muted-foreground/40'
                          }`}
                        >
                          {subStatus === 'completed' ? <Check className="w-3 h-3 mt-0.5 flex-shrink-0 text-emerald-400" /> :
                           subStatus === 'running' ? <Loader2 className="w-3 h-3 mt-0.5 flex-shrink-0 animate-spin text-primary" /> :
                           <Circle className="w-2 h-2 mt-1 flex-shrink-0 text-muted-foreground/30" />}
                          <span className="leading-snug">{sub}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Sidebar: Metrics + Audit */}
        <div className="overflow-y-auto pb-4 scrollbar-thin space-y-4">
          <MetricsPanel metrics={metrics} isRunning={pipelineRunning} />
          {findings.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold flex items-center gap-1.5 mb-2">
                <Shield className="w-3 h-3 text-amber-400" /> Audit
              </h3>
              <AuditPanel
                findings={findings}
                auditScore={auditScore}
                totalChecks={totalChecks}
                passedChecks={passedChecks}
              />
            </div>
          )}
          {/* Current phase details */}
          {currentPhase >= 0 && currentPhase < PHASES_DEF.length && (
            <div className="rounded-xl border border-border/30 bg-background/20 p-3 space-y-2">
              <h3 className="text-xs font-semibold flex items-center gap-1.5">
                <AppIcon name={PHASES_DEF[currentPhase].icon} className="w-3 h-3 text-primary" />
                Phase {currentPhase + 1} Details
              </h3>
              <p className="text-[10px] text-muted-foreground leading-relaxed">
                {PHASES_DEF[currentPhase].desc}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ─── Activity Log (collapsible) ─── */}
      <div className="px-4 sm:px-6 flex-shrink-0">
        <button
          onClick={() => setShowLog(v => !v)}
          className="w-full flex items-center justify-between py-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <span className="flex items-center gap-1.5 font-medium">
            {showLog ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
            Activity Log ({log.length})
          </span>
          <ChevronDown className={`w-3 h-3 transition-transform ${showLog ? 'rotate-180' : ''}`} />
        </button>
        {showLog && (
          <div className="max-h-48 overflow-y-auto mb-2">
            <ActivityLog entries={log} />
          </div>
        )}
      </div>

      {/* ─── Bottom Control Bar ─── */}
      <div className="flex-shrink-0 border-t border-border/30 glass-strong px-4 sm:px-6 py-2.5 flex items-center gap-3 flex-wrap z-20">
        {/* Pause / Resume */}
        <button
          onClick={onPauseResume}
          disabled={!pipelineRunning}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed ${
            isPaused
              ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
              : 'bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20'
          }`}
        >
          {isPaused ? <><Play className="w-3.5 h-3.5" /> Resume</> : <><Pause className="w-3.5 h-3.5" /> Pause</>}
        </button>

        {/* Speed control */}
        <div className="flex items-center gap-1 border border-border/30 rounded-lg px-2 py-1">
          <Gauge className="w-3 h-3 text-muted-foreground" />
          {[0.5, 1, 2, 5].map(s => (
            <button
              key={s}
              onClick={() => onSpeedChange(s)}
              className={`px-2 py-0.5 rounded text-[10px] font-bold transition-all ${
                speed === s
                  ? 'bg-primary/20 text-primary border border-primary/30'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/20'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>

        <div className="flex-1" />

        {/* Audit button */}
        <button
          onClick={onRunAudit}
          disabled={pipelineRunning}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-amber-500/20 bg-amber-500/5 text-xs text-amber-400 hover:bg-amber-500/10 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Shield className="w-3 h-3" />
          <span className="hidden sm:inline">Run Audit</span>
        </button>

        {/* Export */}
        <button
          onClick={onExport}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border/30 bg-background/30 text-xs text-muted-foreground hover:text-foreground transition-all"
        >
          <Download className="w-3 h-3" />
          <span className="hidden sm:inline">Export</span>
        </button>
      </div>
    </div>
  );
}
