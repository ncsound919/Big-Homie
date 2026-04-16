/**
 * Shared data module for trending GitHub repositories
 * Single source of truth for tool/repo metadata across components
 */

export interface TrendingRepoData {
  name: string;
  repo: string;
  stars: number; // Numeric star count for calculations
  description: string;
  category: 'browser' | 'agent' | 'orchestration';
  icon: string;
  color: string;
  highlights: string[]; // Key feature highlights
}

/**
 * Format star count for display (e.g., 86000 -> "86k")
 */
export function formatStars(stars: number): string {
  if (stars >= 1000) {
    const k = stars / 1000;
    return k % 1 === 0 ? `${k}k` : `${k.toFixed(1)}k`;
  }
  return stars.toString();
}

/**
 * Calculate total stars across all repos
 */
export function getTotalStars(repos: TrendingRepoData[]): number {
  return repos.reduce((sum, r) => sum + r.stars, 0);
}

/**
 * Trending GitHub repositories for AI browser automation and coding agents (2025)
 */
export const TRENDING_REPOS: TrendingRepoData[] = [
  // ═══════════════════════════════════════════
  // BROWSER AUTOMATION
  // ═══════════════════════════════════════════
  {
    name: 'browser-use',
    repo: 'browser-use/browser-use',
    stars: 86000,
    description: 'The #1 AI browser automation — natural language control with LLM-driven browsing',
    category: 'browser',
    icon: 'brain',
    color: 'text-pink-500',
    highlights: ['Model-agnostic', 'Stealth mode', 'Multi-step tasks'],
  },
  {
    name: 'Lightpanda',
    repo: 'lightpanda-io/browser',
    stars: 28000,
    description: 'Blazing-fast headless browser built in Zig for AI-first automation',
    category: 'browser',
    icon: 'zap',
    color: 'text-amber-400',
    highlights: ['Ultra-fast', 'AI-optimized', 'Low-level APIs'],
  },
  {
    name: 'Skyvern',
    repo: 'Skyvern-AI/skyvern',
    stars: 21000,
    description: 'LLM + computer vision platform for complex automation workflows',
    category: 'browser',
    icon: 'eye',
    color: 'text-purple-400',
    highlights: ['No selectors', 'CAPTCHA solving', 'Self-adapting'],
  },
  {
    name: 'Maxun',
    repo: 'getmaxun/maxun',
    stars: 15000,
    description: 'No-code AI platform turning websites into structured APIs',
    category: 'browser',
    icon: 'layout',
    color: 'text-rose-400',
    highlights: ['Self-healing', 'No-code', 'API generation'],
  },
  {
    name: 'Nanobrowser',
    repo: 'nicholasgriffintn/nanobrowser',
    stars: 13000,
    description: 'Privacy-centric Chrome extension for multi-agent AI automation',
    category: 'browser',
    icon: 'chrome',
    color: 'text-blue-400',
    highlights: ['Privacy-first', 'Multi-agent', 'Own API keys'],
  },
  {
    name: 'Stagehand',
    repo: 'browserbase/stagehand',
    stars: 12000,
    description: 'Next-gen orchestration for AI-controlled browsers with visual programming',
    category: 'browser',
    icon: 'wand',
    color: 'text-indigo-400',
    highlights: ['Visual builder', 'Multi-agent', 'Enterprise'],
  },
  {
    name: 'Steel Browser',
    repo: 'AskSteelAI/steel-browser',
    stars: 6800,
    description: 'Open-source browser sandbox for AI agents — automate at scale',
    category: 'browser',
    icon: 'server',
    color: 'text-slate-400',
    highlights: ['High concurrency', 'Cloud-native', 'Session management'],
  },

  // ═══════════════════════════════════════════
  // AI CODING AGENTS
  // ═══════════════════════════════════════════
  {
    name: 'OpenHands',
    repo: 'All-Hands-AI/OpenHands',
    stars: 45000,
    description: 'Multi-agent framework for autonomous software engineering',
    category: 'agent',
    icon: 'hand',
    color: 'text-amber-400',
    highlights: ['87% PR acceptance', 'Multi-agent', 'Full repo autonomy'],
  },
  {
    name: 'AutoGen',
    repo: 'microsoft/autogen',
    stars: 35000,
    description: "Microsoft's framework for conversational multi-agent developer systems",
    category: 'agent',
    icon: 'bot',
    color: 'text-purple-400',
    highlights: ['Microsoft-backed', 'Multi-agent', 'Enterprise ready'],
  },
  {
    name: 'CrewAI',
    repo: 'crewAIInc/crewAI',
    stars: 25000,
    description: 'Team of AI agents workflow with planner, coder, reviewer roles',
    category: 'agent',
    icon: 'users',
    color: 'text-cyan-400',
    highlights: ['Role-based', 'Collaborative', 'Task delegation'],
  },
  {
    name: 'Aider',
    repo: 'paul-gauthier/aider',
    stars: 22000,
    description: 'CLI-based AI pair programmer that edits code in your local repo',
    category: 'agent',
    icon: 'terminal',
    color: 'text-green-400',
    highlights: ['Local-first', 'Git-aware', 'Privacy control'],
  },
  {
    name: 'SWE-Agent',
    repo: 'princeton-nlp/SWE-agent',
    stars: 18000,
    description: 'Autonomous agent for bug fixes, code reviews, and generation',
    category: 'agent',
    icon: 'bug',
    color: 'text-red-400',
    highlights: ['Bug fixing', 'Code review', 'Test generation'],
  },

  // ═══════════════════════════════════════════
  // ORCHESTRATION
  // ═══════════════════════════════════════════
  {
    name: 'LangChain',
    repo: 'langchain-ai/langchain',
    stars: 95000,
    description: 'Swiss Army knife for chaining LLMs, APIs, and tools into agents',
    category: 'orchestration',
    icon: 'link',
    color: 'text-emerald-400',
    highlights: ['Composable', 'Tool integration', 'RAG support'],
  },
  {
    name: 'n8n',
    repo: 'n8n-io/n8n',
    stars: 50000,
    description: 'Visual no-code workflow automation with native LLM support',
    category: 'orchestration',
    icon: 'workflow',
    color: 'text-orange-400',
    highlights: ['Visual builder', '400+ integrations', 'Self-hosted'],
  },
  {
    name: 'Langflow',
    repo: 'langflow-ai/langflow',
    stars: 35000,
    description: 'Drag-and-drop visual designer for agentic RAG workflows',
    category: 'orchestration',
    icon: 'sparkles',
    color: 'text-violet-400',
    highlights: ['Visual RAG', 'Code-free', 'Python export'],
  },
  {
    name: 'Daytona',
    repo: 'daytonaio/daytona',
    stars: 15000,
    description: 'Secure infrastructure for executing AI-generated code',
    category: 'orchestration',
    icon: 'container',
    color: 'text-blue-400',
    highlights: ['Secure sandboxes', 'Git integration', 'Multi-cloud'],
  },
  {
    name: 'LangGraph',
    repo: 'langchain-ai/langgraph',
    stars: 8000,
    description: 'Multi-agent workflow orchestration with stateful, cyclical graphs',
    category: 'orchestration',
    icon: 'git-branch',
    color: 'text-teal-400',
    highlights: ['Stateful workflows', 'Cyclical graphs', 'Human-in-the-loop'],
  },
];

/**
 * Get repos filtered by category
 */
export function getReposByCategory(category: TrendingRepoData['category'] | 'all'): TrendingRepoData[] {
  if (category === 'all') return TRENDING_REPOS;
  return TRENDING_REPOS.filter(r => r.category === category);
}

/**
 * Find a repo by name
 */
export function findRepoByName(name: string): TrendingRepoData | undefined {
  return TRENDING_REPOS.find(r => r.name.toLowerCase() === name.toLowerCase());
}
