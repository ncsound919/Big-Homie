'use client';

import { useState, useMemo } from 'react';
import { AppIcon } from '@/lib/icons';
import { formatStars } from '@/lib/trending-repos';
import { ChevronRight, ExternalLink, Star, TrendingUp } from 'lucide-react';

export interface ToolInfo {
  name: string;
  icon: string;
  color: string;
  description: string;
  strengths: string[];
  category: 'browser-automation' | 'ai-powered' | 'no-code' | 'ai-agents' | 'orchestration';
  integrated: boolean;
  trending?: boolean;
  stars?: number; // Numeric star count for calculations
  repo?: string;
}

const TOOLS: ToolInfo[] = [
  // ═══════════════════════════════════════════
  // BROWSER AUTOMATION FRAMEWORKS
  // ═══════════════════════════════════════════
  {
    name: 'Playwright',
    icon: 'monitor',
    color: 'text-green-400',
    description: 'Cross-browser testing with Chromium, Firefox, and WebKit via a single API.',
    strengths: ['Multi-browser', 'Auto-wait', 'Network interception', 'Video recording'],
    category: 'browser-automation',
    integrated: true,
  },
  {
    name: 'Selenium',
    icon: 'globe',
    description: 'The original open-source browser automation framework supporting every major browser.',
    color: 'text-blue-400',
    strengths: ['Universal browser support', 'Multi-language bindings', 'Mature ecosystem', 'Grid support'],
    category: 'browser-automation',
    integrated: true,
  },
  {
    name: 'Puppeteer',
    icon: 'mouse-pointer',
    color: 'text-cyan-400',
    description: 'Node.js library controlling Chrome/Chromium via Chrome DevTools Protocol.',
    strengths: ['Fast execution', 'PDF generation', 'Screenshots', 'Dynamic content scraping'],
    category: 'browser-automation',
    integrated: true,
  },
  {
    name: 'Lightpanda',
    icon: 'zap',
    color: 'text-amber-400',
    description: 'Blazing-fast headless browser built in Zig, designed for AI-first automation workflows.',
    strengths: ['Ultra-fast execution', 'AI-optimized APIs', 'Low-level control', 'Deterministic browsing'],
    category: 'browser-automation',
    integrated: false,
    trending: true,
    stars: 28000,
    repo: 'lightpanda-io/browser',
  },
  {
    name: 'Steel Browser',
    icon: 'server',
    color: 'text-slate-400',
    description: 'Open-source browser sandbox for AI agents — automate at scale without infrastructure headaches.',
    strengths: ['High concurrency', 'LLM integration', 'Cloud-native', 'Session management'],
    category: 'browser-automation',
    integrated: false,
    trending: true,
    stars: 6800,
    repo: 'AskSteelAI/steel-browser',
  },
  {
    name: 'Cypress',
    icon: 'test-tube',
    color: 'text-emerald-400',
    description: 'Excels at web testing with simple setup and a great debugging experience.',
    strengths: ['Time-travel debugging', 'Auto-reload', 'Network stubbing', 'Visual testing'],
    category: 'browser-automation',
    integrated: false,
  },

  // ═══════════════════════════════════════════
  // AI-POWERED AUTOMATION (Trending 2025)
  // ═══════════════════════════════════════════
  {
    name: 'browser-use',
    icon: 'brain',
    color: 'text-pink-500',
    description: 'The #1 AI browser automation library — natural language control with LLM-driven browsing.',
    strengths: ['86k+ stars', 'Model-agnostic', 'Stealth mode', 'Natural language commands'],
    category: 'ai-powered',
    integrated: true,
    trending: true,
    stars: 86000,
    repo: 'browser-use/browser-use',
  },
  {
    name: 'Skyvern',
    icon: 'eye',
    color: 'text-purple-400',
    description: 'LLM + computer vision platform handling complex workflows including CAPTCHA and 2FA.',
    strengths: ['No selectors needed', 'Self-adapting', 'CAPTCHA solving', 'Anti-bot detection'],
    category: 'ai-powered',
    integrated: true,
    trending: true,
    stars: 21000,
    repo: 'Skyvern-AI/skyvern',
  },
  {
    name: 'Stagehand',
    icon: 'wand',
    color: 'text-indigo-400',
    description: 'Next-gen orchestration for AI-controlled browsers with visual programming and multi-step workflows.',
    strengths: ['Visual workflow builder', 'Multi-agent chaining', 'Step-by-step replay', 'Enterprise ready'],
    category: 'ai-powered',
    integrated: false,
    trending: true,
    stars: 12000,
    repo: 'browserbase/stagehand',
  },
  {
    name: 'Nanobrowser',
    icon: 'chrome',
    color: 'text-blue-400',
    description: 'Privacy-centric Chrome extension for multi-agent AI automation — use your own LLM keys.',
    strengths: ['Privacy-first', 'Multi-agent orchestration', 'Own API keys', 'Local execution'],
    category: 'ai-powered',
    integrated: false,
    trending: true,
    stars: 13000,
    repo: 'nicholasgriffintn/nanobrowser',
  },
  {
    name: 'Maxun',
    icon: 'layout',
    color: 'text-rose-400',
    description: 'No-code AI platform turning websites into structured APIs with self-healing selectors.',
    strengths: ['Self-healing selectors', 'API generation', 'No-code builder', 'Batch crawling'],
    category: 'ai-powered',
    integrated: false,
    trending: true,
    stars: 15000,
    repo: 'getmaxun/maxun',
  },
  {
    name: 'Firecrawl',
    icon: 'flame',
    color: 'text-orange-400',
    description: 'Combines scraping and browser automation for extracting structured data from dynamic sites.',
    strengths: ['Structured data extraction', 'Dynamic site support', 'Batch processing', 'API-first'],
    category: 'ai-powered',
    integrated: true,
  },

  // ═══════════════════════════════════════════
  // AI CODING AGENTS (New Category - Trending 2025)
  // ═══════════════════════════════════════════
  {
    name: 'OpenHands',
    icon: 'hand',
    color: 'text-amber-400',
    description: 'Powerful multi-agent framework for autonomous software engineering — opens issues, fixes bugs, submits PRs.',
    strengths: ['87% PR acceptance', 'Multi-agent (planner/coder/reviewer)', 'Full repo autonomy', 'CI/CD integration'],
    category: 'ai-agents',
    integrated: false,
    trending: true,
    stars: 45000,
    repo: 'All-Hands-AI/OpenHands',
  },
  {
    name: 'CrewAI',
    icon: 'users',
    color: 'text-cyan-400',
    description: 'Team of AI agents workflow — planner, coder, reviewer roles collaborating on complex projects.',
    strengths: ['Role-based agents', 'Multi-stage projects', 'Collaborative coding', 'Task delegation'],
    category: 'ai-agents',
    integrated: false,
    trending: true,
    stars: 25000,
    repo: 'crewAIInc/crewAI',
  },
  {
    name: 'Aider',
    icon: 'terminal',
    color: 'text-green-400',
    description: 'CLI-based AI pair programmer that edits code in your local repository using LLMs.',
    strengths: ['Local-first', 'Git-aware', 'Multi-file edits', 'Privacy control'],
    category: 'ai-agents',
    integrated: false,
    trending: true,
    stars: 22000,
    repo: 'paul-gauthier/aider',
  },
  {
    name: 'SWE-Agent',
    icon: 'bug',
    color: 'text-red-400',
    description: 'Autonomous agent for software engineering tasks — bug fixes, code reviews, and generation.',
    strengths: ['Bug fixing', 'Code review automation', 'Test generation', 'Issue resolution'],
    category: 'ai-agents',
    integrated: false,
    trending: true,
    stars: 18000,
    repo: 'princeton-nlp/SWE-agent',
  },
  {
    name: 'AutoGen',
    icon: 'bot',
    color: 'text-purple-400',
    description: 'Microsoft\'s framework for conversational multi-agent developer systems.',
    strengths: ['Microsoft-backed', 'Multi-agent conversations', 'Extensible', 'Enterprise ready'],
    category: 'ai-agents',
    integrated: false,
    trending: true,
    stars: 35000,
    repo: 'microsoft/autogen',
  },

  // ═══════════════════════════════════════════
  // ORCHESTRATION & INFRASTRUCTURE (New Category)
  // ═══════════════════════════════════════════
  {
    name: 'LangChain',
    icon: 'link',
    color: 'text-emerald-400',
    description: 'Swiss Army knife for chaining LLMs, APIs, tools, and databases into higher-level agents.',
    strengths: ['Composable chains', 'Tool integration', 'Memory management', 'RAG support'],
    category: 'orchestration',
    integrated: true,
    trending: true,
    stars: 95000,
    repo: 'langchain-ai/langchain',
  },
  {
    name: 'LangGraph',
    icon: 'git-branch',
    color: 'text-teal-400',
    description: 'Multi-agent workflow orchestration with stateful, cyclical agent graphs.',
    strengths: ['Stateful workflows', 'Cyclical graphs', 'Human-in-the-loop', 'Persistent memory'],
    category: 'orchestration',
    integrated: false,
    trending: true,
    stars: 8000,
    repo: 'langchain-ai/langgraph',
  },
  {
    name: 'n8n',
    icon: 'workflow',
    color: 'text-orange-400',
    description: 'Visual no-code workflow automation with native LLM/agent support for end-to-end pipelines.',
    strengths: ['Visual builder', 'LLM nodes', '400+ integrations', 'Self-hosted'],
    category: 'orchestration',
    integrated: false,
    trending: true,
    stars: 50000,
    repo: 'n8n-io/n8n',
  },
  {
    name: 'Langflow',
    icon: 'sparkles',
    color: 'text-violet-400',
    description: 'Drag-and-drop visual designer for agentic RAG and coding workflows.',
    strengths: ['Visual RAG builder', 'Code-free agents', 'Component library', 'Export to Python'],
    category: 'orchestration',
    integrated: false,
    trending: true,
    stars: 35000,
    repo: 'langflow-ai/langflow',
  },
  {
    name: 'Daytona',
    icon: 'container',
    color: 'text-blue-400',
    description: 'Secure infrastructure for executing AI-generated code with isolated agent workspaces.',
    strengths: ['Secure sandboxes', 'Dev environments', 'Git integration', 'Multi-cloud'],
    category: 'orchestration',
    integrated: false,
    trending: true,
    stars: 15000,
    repo: 'daytonaio/daytona',
  },

  // ═══════════════════════════════════════════
  // NO-CODE / LOW-CODE
  // ═══════════════════════════════════════════
  {
    name: 'Axiom.ai',
    icon: 'box',
    color: 'text-violet-400',
    description: 'No-code browser bot builder — like Zapier for browsers.',
    strengths: ['Zero code needed', 'Cloud execution', 'Template library', 'Scheduling'],
    category: 'no-code',
    integrated: false,
  },
  {
    name: 'Browserflow',
    icon: 'git-merge',
    color: 'text-teal-400',
    description: 'Chrome extension to build visual automation flows by recording clicks and actions.',
    strengths: ['Visual builder', 'Record & replay', 'Cloud runs', 'Data extraction'],
    category: 'no-code',
    integrated: false,
  },
  {
    name: 'Bardeen AI',
    icon: 'star',
    color: 'text-yellow-400',
    description: 'AI-assisted no-code automation tool for browser workflows.',
    strengths: ['AI suggestions', 'App integrations', 'Pre-built playbooks', 'Scraping'],
    category: 'no-code',
    integrated: false,
  },
  {
    name: 'UIVision',
    icon: 'scan',
    color: 'text-lime-400',
    description: 'Free, runs locally — handles clicking buttons, scraping data, and filling forms.',
    strengths: ['Free & local', 'Visual automation', 'XPath & image find', 'Macro recording'],
    category: 'no-code',
    integrated: false,
  },
];

const CATEGORIES = [
  { id: 'all' as const, label: 'All Tools', icon: 'layers', color: 'text-primary' },
  { id: 'browser-automation' as const, label: 'Browser Automation', icon: 'monitor', color: 'text-green-400' },
  { id: 'ai-powered' as const, label: 'AI-Powered', icon: 'brain', color: 'text-purple-400' },
  { id: 'ai-agents' as const, label: 'AI Coding Agents', icon: 'bot', color: 'text-amber-400' },
  { id: 'orchestration' as const, label: 'Orchestration', icon: 'git-branch', color: 'text-teal-400' },
  { id: 'no-code' as const, label: 'No-Code', icon: 'layout', color: 'text-violet-400' },
];

type CategoryFilter = 'all' | ToolInfo['category'];

export default function ToolEcosystem() {
  const [filter, setFilter] = useState<CategoryFilter>('all');
  const [expandedTool, setExpandedTool] = useState<string | null>(null);

  const filtered = useMemo(() => filter === 'all' ? TOOLS : TOOLS.filter(t => t.category === filter), [filter]);
  const integratedCount = useMemo(() => TOOLS.filter(t => t.integrated).length, []);
  const trendingCount = useMemo(() => TOOLS.filter(t => t.trending).length, []);

  return (
    <div className="w-full rounded-2xl border border-border/30 bg-background/20 overflow-hidden">
      {/* Header */}
      <div className="px-4 sm:px-6 py-4 border-b border-border/30">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <AppIcon name="plug" className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-bold text-foreground">Tool Ecosystem</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-pink-500/10 border border-pink-500/20 text-[9px] font-bold text-pink-400">
              <TrendingUp className="w-2.5 h-2.5" />
              {trendingCount} Trending
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[9px] font-bold text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {integratedCount} Integrated
            </span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          AgentBrowser integrates trending AI agents, browser automation, and orchestration tools from GitHub&apos;s top repositories.
        </p>
      </div>

      {/* Category Filter */}
      <div className="px-4 sm:px-6 py-3 border-b border-border/20 flex flex-wrap gap-2">
        {CATEGORIES.map(cat => (
          <button
            key={cat.id}
            onClick={() => setFilter(cat.id)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all duration-200 hover:scale-105 active:scale-95 ${
              filter === cat.id
                ? 'bg-primary/15 text-primary border border-primary/30'
                : 'bg-muted/30 text-muted-foreground border border-transparent hover:border-border/40 hover:text-foreground'
            }`}
          >
            <AppIcon name={cat.icon} className={`w-3 h-3 ${filter === cat.id ? 'text-primary' : cat.color}`} />
            {cat.label}
          </button>
        ))}
      </div>

      {/* Tools Grid */}
      <div className="px-4 sm:px-6 py-4 grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-[480px] overflow-y-auto">
        {filtered.map(tool => {
          const isExpanded = expandedTool === tool.name;
          return (
            <div
              key={tool.name}
              role="button"
              tabIndex={0}
              onClick={() => setExpandedTool(isExpanded ? null : tool.name)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setExpandedTool(isExpanded ? null : tool.name);
                }
              }}
              className={`text-left p-3 rounded-xl border transition-all duration-200 hover:scale-[1.01] active:scale-[0.99] cursor-pointer ${
                isExpanded
                  ? 'border-primary/40 bg-primary/5'
                  : tool.trending
                  ? 'border-pink-500/20 bg-pink-500/5 hover:border-pink-500/30'
                  : tool.integrated
                  ? 'border-emerald-500/20 bg-emerald-500/5 hover:border-emerald-500/30'
                  : 'border-border/30 bg-background/30 hover:border-border/50'
              }`}
            >
              <div className="flex items-start gap-2.5">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  tool.trending ? 'bg-pink-500/10' : tool.integrated ? 'bg-emerald-500/10' : 'bg-muted/20'
                }`}>
                  <AppIcon name={tool.icon} className={`w-4 h-4 ${tool.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-xs font-semibold text-foreground">{tool.name}</span>
                    {tool.stars && (
                      <span className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded text-[8px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        <Star className="w-2 h-2" />
                        {formatStars(tool.stars)}
                      </span>
                    )}
                    {tool.trending && (
                      <span className="px-1 py-0.5 rounded text-[8px] font-bold bg-pink-500/10 text-pink-400 border border-pink-500/30">
                        TRENDING
                      </span>
                    )}
                    {tool.integrated && (
                      <span className="px-1 py-0.5 rounded text-[8px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        INTEGRATED
                      </span>
                    )}
                    <ChevronRight className={`w-2.5 h-2.5 text-muted-foreground/40 ml-auto flex-shrink-0 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`} />
                  </div>
                  <p className="text-[10px] text-muted-foreground leading-snug mt-0.5 line-clamp-2">
                    {tool.description}
                  </p>
                </div>
              </div>

              {/* Expanded strengths */}
              {isExpanded && (
                <div className="mt-2.5 pt-2.5 border-t border-border/20 animate-fade-in-up">
                  <div className="text-[9px] text-muted-foreground uppercase tracking-wider font-medium mb-1.5">Key Strengths</div>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {tool.strengths.map((s, i) => (
                      <span key={i} className={`px-2 py-0.5 rounded-md text-[9px] font-medium ${
                        tool.trending
                          ? 'bg-pink-500/10 text-pink-400 border border-pink-500/20'
                          : tool.integrated
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-muted/30 text-muted-foreground border border-border/20'
                      }`}>
                        {s}
                      </span>
                    ))}
                  </div>
                  {tool.repo && (
                    <a
                      href={`https://github.com/${tool.repo}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[9px] font-medium bg-muted/30 text-muted-foreground hover:text-foreground hover:bg-muted/50 border border-border/20 transition-colors"
                    >
                      <ExternalLink className="w-2.5 h-2.5" />
                      View on GitHub
                    </a>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer stats */}
      <div className="px-4 sm:px-6 py-3 border-t border-border/20 flex items-center justify-between flex-wrap gap-2">
        <span className="text-[10px] text-muted-foreground">
          {filtered.length} tool{filtered.length !== 1 ? 's' : ''} · {filtered.filter(t => t.trending).length} trending · {filtered.filter(t => t.integrated).length} integrated
        </span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-[9px] text-pink-400">
            <TrendingUp className="w-2.5 h-2.5" /> Trending
          </span>
          <span className="flex items-center gap-1 text-[9px] text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Integrated
          </span>
          <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
            <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/30" /> Available
          </span>
        </div>
      </div>
    </div>
  );
}
