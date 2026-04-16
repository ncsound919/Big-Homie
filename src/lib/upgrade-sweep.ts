import { TRENDING_REPOS, type TrendingRepoData } from '@/lib/trending-repos';

export interface UpgradeSweepTarget {
  id: string;
  name: string;
  icon: string;
  color: string;
  summary: string;
  categories: TrendingRepoData['category'][];
  goals: string[];
}

export interface UpgradeSweepRecommendation {
  targetId: string;
  targetName: string;
  icon: string;
  color: string;
  summary: string;
  goals: string[];
  recommendedRepos: Array<TrendingRepoData & { why: string; score: number }>;
}

export type ApprovalTier = 'auto' | 'review' | 'manual';

export interface UpgradeApprovalPlan {
  tier: ApprovalTier;
  approvalRequired: boolean;
  autoExecute: boolean;
  rationale: string;
}

export interface UpgradeImplementationReport {
  finishedAt: string;
  durationSeconds: number;
  outcome: 'success' | 'partial' | 'failure';
  touchedSystems: string[];
  summary: string;
  followUp: string[];
  model?: string;
  costUsd?: number;
}

export interface UpgradeLaunchRequest {
  requestId: string;
  createdAt: string;
  requestedBy: string;
  targetId: string;
  targetName: string;
  summary: string;
  requestMessage: string;
  approvalTier: ApprovalTier;
  approvalRequired: boolean;
  autoExecute: boolean;
  approvalRationale: string;
  status: 'queued' | 'awaiting_approval' | 'running' | 'completed' | 'failed';
  recommendedRepos: Array<TrendingRepoData & { why: string; score: number }>;
  report?: UpgradeImplementationReport;
}

const SWEEP_TARGETS: UpgradeSweepTarget[] = [
  {
    id: 'agentbrowser',
    name: 'AgentBrowser',
    icon: 'layout-dashboard',
    color: 'text-cyan-400',
    summary: 'Customer-facing command center that needs stronger browser automation, orchestration, and self-healing UI flows.',
    categories: ['browser', 'orchestration', 'agent'],
    goals: ['visual automation', 'workflow control', 'self-healing selectors', 'multi-agent workspaces'],
  },
  {
    id: 'draymond',
    name: 'Draymond',
    icon: 'brain',
    color: 'text-amber-400',
    summary: 'Core orchestrator that needs deeper multi-agent planning, stateful graphs, and automated execution loops.',
    categories: ['agent', 'orchestration', 'browser'],
    goals: ['multi-agent planning', 'stateful workflows', 'tool integration', 'autonomy'],
  },
  {
    id: 'browser-use',
    name: 'Browser Automation Layer',
    icon: 'monitor',
    color: 'text-pink-400',
    summary: 'The automation surface should keep absorbing stronger browser runtimes and self-healing interaction models.',
    categories: ['browser', 'agent'],
    goals: ['faster browser runtime', 'selector healing', 'vision automation'],
  },
  {
    id: 'quality-stack',
    name: 'Quality Stack',
    icon: 'shield',
    color: 'text-emerald-400',
    summary: 'Phaselock, Codegang, and verification layers need stronger autonomous remediation and review agents.',
    categories: ['agent', 'orchestration'],
    goals: ['automated review', 'repair loops', 'stateful verification'],
  },
  {
    id: 'research-content',
    name: 'Research + Content Systems',
    icon: 'sparkles',
    color: 'text-violet-400',
    summary: 'Research and content tools should inherit better orchestration and tool-chaining rather than isolated runs.',
    categories: ['orchestration', 'agent', 'browser'],
    goals: ['workflow chaining', 'RAG support', 'automation'],
  },
];

function scoreRepoForTarget(target: UpgradeSweepTarget, repo: TrendingRepoData): number {
  let score = repo.stars / 10000;
  if (target.categories.includes(repo.category)) score += 6;

  const repoText = `${repo.description} ${repo.highlights.join(' ')}`.toLowerCase();
  for (const goal of target.goals) {
    if (repoText.includes(goal.toLowerCase().split(' ')[0])) {
      score += 1.5;
    }
  }

  return score;
}

function buildReason(target: UpgradeSweepTarget, repo: TrendingRepoData): string {
  const focus = repo.highlights.slice(0, 2).join(', ') || repo.category;
  return `Fits ${target.name} because it improves ${focus.toLowerCase()}.`;
}

function buildRecommendation(target: UpgradeSweepTarget): UpgradeSweepRecommendation {
  const recommendedRepos = [...TRENDING_REPOS]
    .map(repo => ({ ...repo, score: scoreRepoForTarget(target, repo), why: buildReason(target, repo) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);

  return {
    targetId: target.id,
    targetName: target.name,
    icon: target.icon,
    color: target.color,
    summary: target.summary,
    goals: target.goals,
    recommendedRepos,
  };
}

export const MASSIVE_UPGRADE_SWEEP: UpgradeSweepRecommendation[] = SWEEP_TARGETS.map(buildRecommendation);
export const FIRST_WAVE_SWEEP = MASSIVE_UPGRADE_SWEEP.slice(0, 2);

export function determineApprovalPlan(target: UpgradeSweepRecommendation): UpgradeApprovalPlan {
  const categories = new Set(target.recommendedRepos.map(repo => repo.category));
  const isCoreTarget = target.targetId === 'agentbrowser' || target.targetId === 'draymond';
  const hasArchitectureRepo = categories.has('orchestration');

  if (isCoreTarget && hasArchitectureRepo) {
    return {
      tier: 'manual',
      approvalRequired: true,
      autoExecute: false,
      rationale: 'Core architecture target with orchestration-level upgrades. Pause for explicit approval.',
    };
  }

  if (isCoreTarget || hasArchitectureRepo) {
    return {
      tier: 'review',
      approvalRequired: true,
      autoExecute: false,
      rationale: 'Touches orchestration or a core platform. Queue for review before Draymond executes.',
    };
  }

  return {
    tier: 'auto',
    approvalRequired: false,
    autoExecute: true,
    rationale: 'Incremental upgrade with low architecture risk. Draymond can auto-run it.',
  };
}

export function buildUpgradeRequestMessage(target: UpgradeSweepRecommendation): string {
  const repoSummary = target.recommendedRepos
    .map(repo => `${repo.name} (${repo.repo})`)
    .join(', ');

  return [
    `Run an upgrade sweep for ${target.targetName}.`,
    `Target summary: ${target.summary}`,
    `Priority repos: ${repoSummary}`,
    'Assess fit, integrate the strongest improvements, preserve stability, and return an implementation roadmap plus execution summary.',
  ].join(' ');
}