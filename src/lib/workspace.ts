// Workspace mode management, pipeline phase definitions, and build state auto-save.

/* ═══════════════════════════════════════════
   WORKSPACE MODES
   ═══════════════════════════════════════════ */
export type WorkspaceMode = 'build' | 'browse' | 'research' | 'scrape' | 'ventures' | 'security';

export interface WorkspaceModeConfig {
  id: WorkspaceMode;
  label: string;
  icon: string;
  description: string;
  color: string;
}

export const WORKSPACE_MODES: WorkspaceModeConfig[] = [
  { id: 'build', label: 'Build', icon: 'hammer', description: 'Autonomous project builder', color: 'purple' },
  { id: 'browse', label: 'Browse', icon: 'globe', description: 'AI-assisted web browsing', color: 'blue' },
  { id: 'research', label: 'Research', icon: 'search', description: 'Multi-source deep research', color: 'cyan' },
  { id: 'scrape', label: 'Scrape', icon: 'database', description: 'Structured data extraction', color: 'orange' },
  { id: 'ventures', label: 'Ventures', icon: 'rocket', description: 'Sellable products & services', color: 'emerald' },
  { id: 'security', label: 'Security', icon: 'shield', description: 'Security monitoring & settings', color: 'red' },
];

/* ═══════════════════════════════════════════
   PIPELINE PHASES DEFINITION (12 phases)
   ═══════════════════════════════════════════ */
export const PHASES_DEF = [
  {
    id: 1, name: 'AI Research & Planning', icon: 'brain', type: 'build' as const,
    desc: 'OpenHands multi-agent framework analyzes requirements, researches best practices using LangChain, and creates a comprehensive implementation plan.',
    subs: ['OpenHands: Analyze project requirements in depth', 'LangChain: Research similar projects and patterns', 'CrewAI: Identify optimal architecture patterns', 'Create detailed implementation roadmap', 'Define acceptance criteria for each feature'],
    securityCheck: 'prompt-injection' as const,
  },
  {
    id: 2, name: 'Understand What You Need', icon: 'message-square', type: 'build' as const,
    desc: 'The system reads your project description and fills any gaps with intelligent defaults based on your project type.',
    subs: ['Parse your project description', 'Identify missing requirements', 'Generate complete feature list', 'Confirm project scope and constraints'],
    securityCheck: 'prompt-injection' as const,
  },
  {
    id: 3, name: 'Design the System', icon: 'compass', type: 'build' as const,
    desc: 'CrewAI planner and architect agents design the technical architecture, data models, API contracts, and component structure.',
    subs: ['Design database schema and models', 'Plan API endpoints and contracts', 'Define component hierarchy', 'Choose libraries and dependencies', 'Create file and folder structure'],
    securityCheck: 'command-validation' as const,
  },
  {
    id: 4, name: 'Set Up the Foundation', icon: 'layers', type: 'build' as const,
    desc: 'Aider CLI agent creates the project, initializes the codebase, and configures all services inside Daytona secure workspaces.',
    subs: ['Daytona: Initialize secure project workspace', 'Aider: Set up framework and build tooling', 'Configure database and migrations', 'Set up authentication system', 'Connect deployment platform'],
    securityCheck: 'secrets-detection' as const,
  },
  {
    id: 5, name: 'Browser Automation Engine', icon: 'monitor', type: 'build' as const,
    desc: 'Configures trending browser engines: browser-use (86k★), Playwright, Stagehand, Skyvern AI, or Lightpanda for cross-browser capabilities.',
    subs: ['browser-use: Initialize LLM-driven automation engine', 'Stagehand: Configure multi-agent orchestration', 'Set up proxy rotation and anti-detection', 'Lightpanda: Enable cross-browser support matrix', 'Configure screenshot and video recording'],
    securityCheck: 'command-validation' as const,
  },
  {
    id: 6, name: 'Build Core Features', icon: 'box', type: 'build' as const,
    desc: 'OpenHands and SWE-Agent implement the main features with 87% PR acceptance rate — the parts your users will interact with most.',
    subs: ['OpenHands: Implement user authentication flow', 'SWE-Agent: Build main data models and API', 'Create primary user interface', 'Connect front-end to back-end', 'Add input validation and error handling'],
    securityCheck: 'secrets-detection' as const,
  },
  {
    id: 7, name: 'Quality Gate: Core Audit', icon: 'shield', type: 'audit' as const,
    desc: 'AutoGen code reviewer agent performs automatic audit. Security, race conditions, and type safety are verified before proceeding.',
    subs: ['AutoGen: Security vulnerability scan', 'Race condition detection', 'Type safety analysis', 'Auto-fix any issues found', 'Re-audit to confirm fixes'],
    securityCheck: 'secrets-detection' as const,
  },
  {
    id: 8, name: 'AI-Powered Automation Layer', icon: 'sparkles', type: 'build' as const,
    desc: 'Integrates trending AI tools: browser-use (86k★) for natural language commands, Skyvern (21k★) for vision-based automation, Maxun (15k★) for self-healing selectors, and Firecrawl for structured data extraction.',
    subs: ['browser-use: Set up natural language command processing', 'Skyvern: Configure LLM-based vision detection', 'Maxun: Enable self-healing selector system', 'Nanobrowser: Add privacy-centric multi-agent automation', 'Firecrawl: Build structured data extraction pipeline'],
    securityCheck: 'command-validation' as const,
  },
  {
    id: 9, name: 'Build Remaining Features', icon: 'boxes', type: 'build' as const,
    desc: 'With the core verified, Aider and SWE-Agent build out secondary features, edge cases, and polish.',
    subs: ['Implement secondary features', 'Add error handling and edge cases', 'Build settings and preferences', 'Create notification system', 'Add loading states and transitions'],
    securityCheck: 'secrets-detection' as const,
  },
  {
    id: 10, name: 'Performance Optimization', icon: 'gauge', type: 'build' as const,
    desc: 'Dedicated performance agent optimizes bundle size, rendering speed, and resource usage. LangGraph orchestrates parallel optimization workflows.',
    subs: ['LangGraph: Analyze bundle size and tree-shake', 'Optimize rendering with memoization', 'Implement code splitting and lazy loading', 'Optimize database queries and indexing', 'n8n: Add caching at all layers'],
    securityCheck: 'command-validation' as const,
  },
  {
    id: 11, name: 'Quality Gate: Full Audit', icon: 'shield', type: 'audit' as const,
    desc: 'Complete 7-category audit using AutoGen multi-agent system. Nothing ships with known critical issues.',
    subs: ['Static analysis and complexity scan', 'Security vulnerabilities deep scan', 'Code smells and duplication check', 'Race conditions and concurrency audit', 'Memory leak and resource cleanup check', 'Type safety and null check verification', 'Dependency health and CVE scan', 'Auto-fix everything possible', 'Final verification and sign-off'],
    securityCheck: 'secrets-detection' as const,
  },
  {
    id: 12, name: 'Deploy and Deliver', icon: 'rocket', type: 'build' as const,
    desc: 'The finished project is deployed via n8n workflows, tested live with browser-use, and documented. You receive working URLs and access credentials.',
    subs: ['Daytona: Deploy to production environment', 'browser-use: Run live health checks', 'Stagehand: Execute cross-browser smoke tests', 'Langflow: Generate API documentation', 'Create handoff summary and guide'],
    securityCheck: 'secrets-detection' as const,
  },
];

/* ═══════════════════════════════════════════
   BUILD STATE AUTO-SAVE
   ═══════════════════════════════════════════ */
const BUILD_STATE_KEY = 'ab_build_state';

export interface SavedBuildState {
  savedAt: string;
  view: string;
  project: any;
  analysis: any;
  phases: any[];
  currentPhase: number;
  currentSubStep: number;
  metrics: any;
  findings: any[];
  log: any[];
  confidence: number;
  speed: number;
  isPaused: boolean;
  pipelineRunning: boolean;
  techStack: string[];
}

export function saveBuildState(state: SavedBuildState): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(BUILD_STATE_KEY, JSON.stringify(state));
  } catch { /* quota exceeded — silent fail */ }
}

export function loadBuildState(): SavedBuildState | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(BUILD_STATE_KEY);
    if (!raw) return null;
    const state = JSON.parse(raw) as SavedBuildState;
    // Only restore saves < 24h old
    if (Date.now() - new Date(state.savedAt).getTime() > 86_400_000) {
      clearBuildState();
      return null;
    }
    return state;
  } catch {
    return null;
  }
}

export function clearBuildState(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(BUILD_STATE_KEY);
}
