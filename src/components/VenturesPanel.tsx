'use client';

import { useState } from 'react';
import {
  Rocket, DollarSign, Zap, BookOpen, LineChart, Wrench, TrendingUp,
  ArrowRight, CheckCircle2, Clock, AlertCircle, Sparkles, ShoppingCart, ExternalLink,
} from 'lucide-react';

/* ─── Types ─────────────────────────────────────────────── */

interface Venture {
  id: string;
  name: string;
  tagline: string;
  status: 'scaffolded' | 'building' | 'live' | 'beta';
  revenue_model: string;
  pricing: Record<string, string>;
  tools: string[];
  outputs: string[];
  icon: React.ReactNode;
  color: string;
  gradient: string;
  gumroad_url?: string;
  presale?: { enabled: boolean; spots_left?: number; founding_price?: string };
}

interface ComboChain {
  id: string;
  name: string;
  description: string;
  steps: string[];
  output: string;
  est_value: string;
}

/* ─── Data ──────────────────────────────────────────────── */

const VENTURES: Venture[] = [
  {
    id: 'alpha_engine',
    name: 'AlphaEngine',
    tagline: 'Unified financial intelligence — stocks, strategy sims, sports picks',
    status: 'beta',
    revenue_model: 'Subscription',
    pricing: { starter: '$49/mo', pro: '$149/mo', desk: '$299/mo' },
    tools: ['TradingAgents', 'AI Hedge Fund', 'Sports Steve'],
    outputs: ['Stock signals', 'Sports picks', 'Risk reports', 'Audio briefs'],
    icon: <LineChart className="w-5 h-5" />,
    color: 'text-emerald-400',
    gradient: 'from-emerald-500/20 to-emerald-600/5',
    gumroad_url: 'https://tap919.gumroad.com/l/alpha-engine',
    presale: { enabled: true, spots_left: 47, founding_price: '$49' },
  },
  {
    id: 'course_factory',
    name: 'CourseFactory',
    tagline: 'Topic → full course business with curriculum, media, and payments',
    status: 'scaffolded',
    revenue_model: 'Project + Rev Share',
    pricing: { build: '$1,500–$8,000', rev_share: '10–30%' },
    tools: ['DeepResearch', 'NotebookLM', 'MediaFactory', 'Stripe'],
    outputs: ['Curriculum', 'Video lessons', 'Interactive assets', 'Storefront'],
    icon: <BookOpen className="w-5 h-5" />,
    color: 'text-blue-400',
    gradient: 'from-blue-500/20 to-blue-600/5',
    gumroad_url: 'https://tap919.gumroad.com/l/course-factory',
  },
  {
    id: 'visual_workflow_studio',
    name: 'VisualWorkflowStudio',
    tagline: 'No-code workflow builder for customer automations',
    status: 'scaffolded',
    revenue_model: 'Setup + Usage',
    pricing: { setup: '$750–$4,000', usage: 'Per execution' },
    tools: ['n8n', 'browser-use', 'Skyvern', 'DeployEngine'],
    outputs: ['Workflow definitions', 'Execution history', 'Cost estimates'],
    icon: <Zap className="w-5 h-5" />,
    color: 'text-purple-400',
    gradient: 'from-purple-500/20 to-purple-600/5',
    gumroad_url: 'https://tap919.gumroad.com/l/workflow-studio',
  },
  {
    id: 'research_to_revenue',
    name: 'ResearchToRevenue',
    tagline: 'Turn research into monetizable IP bundles — ebooks, courses, funnels',
    status: 'scaffolded',
    revenue_model: 'Project Fee',
    pricing: { project: '$1,000–$6,000' },
    tools: ['DeepResearch', 'Book Publishing', 'MediaFactory', 'Stripe'],
    outputs: ['Ebook packages', 'Offer stacks', 'Video promos', 'Sales funnels'],
    icon: <TrendingUp className="w-5 h-5" />,
    color: 'text-amber-400',
    gradient: 'from-amber-500/20 to-amber-600/5',
    gumroad_url: 'https://tap919.gumroad.com/l/research-to-revenue',
  },
  {
    id: 'self_healing_mesh',
    name: 'SelfHealingMesh',
    tagline: 'Autonomous repair and validation for broken repos and infra',
    status: 'scaffolded',
    revenue_model: 'Per-Repo License',
    pricing: { per_repo: '$29/mo', fleet: '$199/mo' },
    tools: ['Overlay Mesh', 'Phaselock', 'DeployEngine', 'OpenHands'],
    outputs: ['Repair plans', 'Validation reports', 'Auto-patches'],
    icon: <Wrench className="w-5 h-5" />,
    color: 'text-red-400',
    gradient: 'from-red-500/20 to-red-600/5',
    gumroad_url: 'https://tap919.gumroad.com/l/self-healing-mesh',
  },
];

const COMBO_CHAINS: ComboChain[] = [
  {
    id: 'music_to_money',
    name: 'Music → Money',
    description: 'Research trending sounds → generate beats → produce video → publish → collect royalties',
    steps: ['DeepResearch', 'VoiceBox', 'MediaFactory', 'Book Publishing', 'Stripe'],
    output: 'Royalty-generating music content pipeline',
    est_value: '$500–$5,000/mo passive',
  },
  {
    id: 'lesson_to_empire',
    name: 'Lesson → Empire',
    description: 'Research topic → build curriculum → produce video lessons → launch course → automate enrollment',
    steps: ['DeepResearch', 'CourseFactory', 'MediaFactory', 'DeployEngine', 'Stripe'],
    output: 'Full course business from a single topic',
    est_value: '$2,000–$20,000/launch',
  },
  {
    id: 'repair_to_replatform',
    name: 'Repair → Replatform',
    description: 'Scan broken repos → diagnose → auto-fix → redeploy → offer as managed service',
    steps: ['SelfHealingMesh', 'OpenHands', 'Phaselock', 'DeployEngine'],
    output: 'Managed repair-as-a-service for dev teams',
    est_value: '$1,000–$10,000/client',
  },
];

/* ─── Status Badge ──────────────────────────────────────── */

function StatusBadge({ status }: { status: Venture['status'] }) {
  const styles: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
    live:       { bg: 'bg-emerald-500/10', text: 'text-emerald-400', icon: <CheckCircle2 className="w-3 h-3" /> },
    beta:       { bg: 'bg-blue-500/10', text: 'text-blue-400', icon: <Sparkles className="w-3 h-3" /> },
    building:   { bg: 'bg-amber-500/10', text: 'text-amber-400', icon: <Clock className="w-3 h-3" /> },
    scaffolded: { bg: 'bg-zinc-500/10', text: 'text-zinc-400', icon: <AlertCircle className="w-3 h-3" /> },
  };
  const s = styles[status] ?? styles.scaffolded;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${s.bg} ${s.text}`}>
      {s.icon} {status}
    </span>
  );
}

/* ─── Venture Card ──────────────────────────────────────── */

function VentureCard({ venture }: { venture: Venture }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`relative overflow-hidden rounded-xl border border-border/40 bg-gradient-to-br ${venture.gradient} backdrop-blur-sm transition-all hover:border-border/60 hover:shadow-lg`}
    >
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-background/40 ${venture.color}`}>
              {venture.icon}
            </div>
            <div>
              <h3 className="font-semibold text-foreground">{venture.name}</h3>
              <p className="text-xs text-muted-foreground">{venture.tagline}</p>
            </div>
          </div>
          <StatusBadge status={venture.status} />
        </div>

        {/* Pricing */}
        <div className="flex flex-wrap gap-2 mb-3">
          {Object.entries(venture.pricing).map(([tier, price]) => (
            <span key={tier} className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-background/30 text-xs">
              <DollarSign className="w-3 h-3 text-emerald-400" />
              <span className="text-muted-foreground capitalize">{tier}:</span>
              <span className="font-medium text-foreground">{price}</span>
            </span>
          ))}
        </div>

        {/* Revenue Model */}
        <div className="text-xs text-muted-foreground mb-3">
          Revenue: <span className="text-foreground font-medium">{venture.revenue_model}</span>
        </div>

        {/* Expand button */}
        <div className="flex items-center justify-between mt-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            <ArrowRight className={`w-3 h-3 transition-transform ${expanded ? 'rotate-90' : ''}`} />
            {expanded ? 'Less' : 'More details'}
          </button>
          
          {/* Buy / Pre-sale Button */}
          {venture.gumroad_url && (
            <a
              href={venture.gumroad_url}
              target="_blank"
              rel="noopener noreferrer"
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                venture.presale?.enabled
                  ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:from-amber-600 hover:to-orange-600 animate-pulse'
                  : 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'
              }`}
            >
              <ShoppingCart className="w-3 h-3" />
              {venture.presale?.enabled ? (
                <>
                  Pre-Sale {venture.presale.founding_price}
                  <span className="text-[10px] opacity-80">({venture.presale.spots_left} left)</span>
                </>
              ) : (
                <>Buy Now <ExternalLink className="w-3 h-3" /></>
              )}
            </a>
          )}
        </div>

        {/* Expanded details */}
        {expanded && (
          <div className="mt-3 pt-3 border-t border-border/30 space-y-2">
            <div>
              <span className="text-xs font-medium text-muted-foreground">Tools:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {venture.tools.map(t => (
                  <span key={t} className="px-2 py-0.5 rounded bg-background/40 text-xs text-foreground">{t}</span>
                ))}
              </div>
            </div>
            <div>
              <span className="text-xs font-medium text-muted-foreground">Outputs:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {venture.outputs.map(o => (
                  <span key={o} className="px-2 py-0.5 rounded bg-background/40 text-xs text-foreground">{o}</span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Combo Chain Card ──────────────────────────────────── */

function ComboCard({ chain }: { chain: ComboChain }) {
  return (
    <div className="rounded-xl border border-border/40 bg-background/10 backdrop-blur-sm p-5 hover:border-border/60 transition-all">
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="w-4 h-4 text-amber-400" />
        <h4 className="font-semibold text-foreground">{chain.name}</h4>
        <span className="ml-auto text-xs font-medium text-emerald-400">{chain.est_value}</span>
      </div>
      <p className="text-xs text-muted-foreground mb-3">{chain.description}</p>
      <div className="flex items-center gap-1 flex-wrap">
        {chain.steps.map((step, i) => (
          <span key={`${chain.id}-${step}-${i}`} className="flex items-center gap-1">
            <span className="px-2 py-0.5 rounded bg-background/40 text-xs text-foreground">{step}</span>
            {i < chain.steps.length - 1 && <ArrowRight className="w-3 h-3 text-muted-foreground" />}
          </span>
        ))}
      </div>
    </div>
  );
}

/* ─── Main Panel ────────────────────────────────────────── */

export default function VenturesPanel() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-emerald-500/10">
          <Rocket className="w-5 h-5 text-emerald-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Ventures & Products</h2>
          <p className="text-xs text-muted-foreground">
            {VENTURES.length} ventures · {COMBO_CHAINS.length} unique combo chains · powered by {new Set(VENTURES.flatMap(v => v.tools)).size}+ tools
          </p>
        </div>
      </div>

      {/* Venture grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {VENTURES.map(v => (
          <VentureCard key={v.id} venture={v} />
        ))}
      </div>

      {/* Combo chains */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-400" />
          Unique Combo Chains — Sellable Goods
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {COMBO_CHAINS.map(c => (
            <ComboCard key={c.id} chain={c} />
          ))}
        </div>
      </div>
    </div>
  );
}
