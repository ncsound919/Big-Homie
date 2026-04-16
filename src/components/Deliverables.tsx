'use client';

import {
  Globe, GitBranch, Database, FileText, TrendingUp, Shield,
  Boxes, BarChart2, ClipboardCheck, CheckCircle2, Circle,
  Workflow, PartyPopper, Wind, Atom, Server, Cloud, Zap, Code2,
  ArrowUpDown, Monitor, Eye, Bot, Copy, Check,
} from 'lucide-react';
import { useState } from 'react';

import type { LucideProps } from 'lucide-react';
import type { ComponentType } from 'react';

interface DeliverablesProps {
  projectName: string;
  techStack: string[];
  metrics: {
    linesOfCode: number;
    filesCreated: number;
    testsPassing: number;
    securityScore: number;
  };
}

const TECH_ICONS: Record<string, { icon: ComponentType<LucideProps>; color: string }> = {
  'Next.js': { icon: Code2, color: 'text-white' },
  'TypeScript': { icon: Code2, color: 'text-blue-400' },
  'Tailwind CSS': { icon: Wind, color: 'text-cyan-400' },
  'Prisma': { icon: Database, color: 'text-emerald-400' },
  'Node.js': { icon: Server, color: 'text-green-400' },
  'React': { icon: Atom, color: 'text-cyan-300' },
  'PostgreSQL': { icon: Database, color: 'text-blue-300' },
  'SQLite': { icon: Database, color: 'text-blue-200' },
  'Vercel': { icon: Cloud, color: 'text-white' },
  'Supabase': { icon: Zap, color: 'text-emerald-300' },
  'Redis': { icon: Server, color: 'text-red-400' },
  'Playwright': { icon: Monitor, color: 'text-green-400' },
  'Puppeteer': { icon: Globe, color: 'text-cyan-400' },
  'Selenium': { icon: Globe, color: 'text-blue-400' },
  'Skyvern': { icon: Eye, color: 'text-purple-400' },
  'BrowserUse': { icon: Bot, color: 'text-pink-400' },
  'Firecrawl': { icon: Zap, color: 'text-orange-400' },
};

const DELIVERABLES: { icon: ComponentType<LucideProps>; color: string; bg: string; name: string; descType: string }[] = [
  { icon: Globe, color: 'text-emerald-400', bg: 'bg-emerald-500/10', name: 'Live Application', descType: 'url' },
  { icon: GitBranch, color: 'text-purple-400', bg: 'bg-purple-500/10', name: 'Source Code', descType: 'repo' },
  { icon: Database, color: 'text-cyan-400', bg: 'bg-cyan-500/10', name: 'Database', descType: 'db' },
  { icon: FileText, color: 'text-amber-400', bg: 'bg-amber-500/10', name: 'Documentation', descType: 'docs' },
  { icon: Monitor, color: 'text-green-400', bg: 'bg-green-500/10', name: 'Cross-Browser Report', descType: 'browser-report' },
  { icon: Shield, color: 'text-orange-400', bg: 'bg-orange-500/10', name: 'Security Report', descType: 'security' },
  { icon: TrendingUp, color: 'text-pink-400', bg: 'bg-pink-500/10', name: 'Analytics', descType: 'analytics' },
  { icon: Eye, color: 'text-violet-400', bg: 'bg-violet-500/10', name: 'Visual Test Results', descType: 'visual-tests' },
  { icon: Bot, color: 'text-sky-400', bg: 'bg-sky-500/10', name: 'Automation Scripts', descType: 'automation' },
];

const CHECKLIST_ITEMS = [
  { label: 'Production deployment verified', done: true },
  { label: 'SSL certificate active', done: true },
  { label: 'Database migrations applied', done: true },
  { label: 'Environment variables configured', done: true },
  { label: 'Health checks passing', done: true },
  { label: 'Error monitoring enabled', done: true },
  { label: 'Performance benchmarks met', done: true },
  { label: 'Security scan cleared', done: true },
];

export default function Deliverables({ projectName, techStack, metrics }: DeliverablesProps) {
  const slug = projectName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const copyToClipboard = (text: string, idx: number) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 1800);
    });
  };

  const getDeliverableDesc = (descType: string) => {
    switch (descType) {
      case 'url': return `https://${slug}.vercel.app`;
      case 'repo': return `github.com/agentbrowser/${slug}`;
      case 'db': return `supabase.com/dashboard/project/${slug}`;
      case 'docs': return 'README, API reference & deployment guide';
      case 'analytics': return `vercel.com/dashboard/analytics/${slug}`;
      case 'security': return 'Full audit report with all checks';
      case 'browser-report': return 'Chromium, Firefox, WebKit compatibility matrix';
      case 'visual-tests': return 'Screenshot diffs across browsers and viewports';
      case 'automation': return 'Playwright/Puppeteer scripts and workflow configs';
      default: return '';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-semibold mb-3">
          <PartyPopper className="w-4 h-4" />
          Project Delivered Successfully
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-foreground">{projectName}</h2>
        <p className="text-sm text-muted-foreground mt-1">Your project is live and ready to use</p>
      </div>

      {/* Deliverables Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {DELIVERABLES.map((del, i) => {
          const desc = getDeliverableDesc(del.descType);
          const isCopyable = ['url', 'repo', 'db', 'analytics'].includes(del.descType);
          return (
            <div
              key={i}
              className="group p-4 rounded-xl border border-border/30 bg-background/20 hover:border-primary/30 hover:bg-primary/5 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
            >
              <div className="flex items-start gap-3">
                <div className={`w-10 h-10 rounded-lg ${del.bg} flex items-center justify-center flex-shrink-0`}>
                  <del.icon className={`w-5 h-5 ${del.color}`} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">{del.name}</p>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <p className="text-xs text-muted-foreground font-mono truncate flex-1">{desc}</p>
                    {isCopyable && (
                      <button
                        onClick={() => copyToClipboard(desc, i)}
                        className="flex-shrink-0 p-0.5 rounded text-muted-foreground/40 hover:text-primary transition-colors"
                        title="Copy to clipboard"
                      >
                        {copiedIdx === i
                          ? <Check className="w-3 h-3 text-emerald-400" />
                          : <Copy className="w-3 h-3" />}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Tech Stack */}
      <div className="p-4 rounded-xl border border-border/30 bg-background/20">
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
          <Boxes className="w-3.5 h-3.5 text-primary" />
          Tech Stack
        </h3>
        <div className="flex flex-wrap gap-2">
          {techStack.map((tech, i) => {
            const meta = TECH_ICONS[tech] || { icon: Code2, color: 'text-muted-foreground' };
            return (
              <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-background/30 border border-border/20 text-xs font-medium text-foreground/80 hover:border-primary/30 transition-colors">
                <meta.icon className={`w-3 h-3 ${meta.color}`} />
                {tech}
              </span>
            );
          })}
        </div>
      </div>

      {/* Stats & Checklist */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Project Statistics */}
        <div className="p-4 rounded-xl border border-border/30 bg-background/20">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <BarChart2 className="w-3.5 h-3.5 text-cyan-400" />
            Project Statistics
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center p-2 rounded-lg bg-background/30">
              <div className="text-xl font-bold text-purple-400">{metrics.linesOfCode.toLocaleString()}</div>
              <div className="text-[9px] text-muted-foreground uppercase">Lines of Code</div>
            </div>
            <div className="text-center p-2 rounded-lg bg-background/30">
              <div className="text-xl font-bold text-cyan-400">{metrics.filesCreated}</div>
              <div className="text-[9px] text-muted-foreground uppercase">Files Created</div>
            </div>
            <div className="text-center p-2 rounded-lg bg-background/30">
              <div className="text-xl font-bold text-emerald-400">{metrics.testsPassing}</div>
              <div className="text-[9px] text-muted-foreground uppercase">Tests Passing</div>
            </div>
            <div className="text-center p-2 rounded-lg bg-background/30">
              <div className="text-xl font-bold text-amber-400">{metrics.securityScore}/100</div>
              <div className="text-[9px] text-muted-foreground uppercase">Security Score</div>
            </div>
          </div>
        </div>

        {/* Deployment Checklist */}
        <div className="p-4 rounded-xl border border-border/30 bg-background/20">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <ClipboardCheck className="w-3.5 h-3.5 text-emerald-400" />
            Deployment Checklist
          </h3>
          <div className="space-y-1.5">
            {CHECKLIST_ITEMS.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                {item.done ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                ) : (
                  <Circle className="w-3.5 h-3.5 text-muted-foreground/30 flex-shrink-0" />
                )}
                <span className={item.done ? 'text-foreground/80' : 'text-muted-foreground'}>{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Architecture Diagram (simplified) */}
      <div className="p-4 rounded-xl border border-border/30 bg-background/20">
        <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
          <Workflow className="w-3.5 h-3.5 text-purple-400" />
          System Architecture
        </h3>
        <div className="flex flex-col items-center gap-2">
          {/* Client Layer */}
          <div className="flex items-center gap-2 flex-wrap justify-center">
            <div className="px-3 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-mono text-cyan-400">Next.js Frontend</div>
          </div>
          <div className="w-px h-4 bg-border/30" />
          <ArrowUpDown className="w-3 h-3 text-muted-foreground/40" />
          <div className="w-px h-4 bg-border/30" />
          {/* API Layer */}
          <div className="flex items-center gap-2 flex-wrap justify-center">
            <div className="px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-[10px] font-mono text-purple-400">API Routes</div>
            <div className="px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-[10px] font-mono text-purple-400">Auth Middleware</div>
          </div>
          <div className="w-px h-4 bg-border/30" />
          <ArrowUpDown className="w-3 h-3 text-muted-foreground/40" />
          <div className="w-px h-4 bg-border/30" />
          {/* Automation Layer */}
          <div className="flex items-center gap-2 flex-wrap justify-center">
            <div className="px-3 py-1.5 rounded-lg bg-green-500/10 border border-green-500/20 text-[10px] font-mono text-green-400">Playwright</div>
            <div className="px-3 py-1.5 rounded-lg bg-sky-500/10 border border-sky-500/20 text-[10px] font-mono text-sky-400">Puppeteer</div>
            <div className="px-3 py-1.5 rounded-lg bg-violet-500/10 border border-violet-500/20 text-[10px] font-mono text-violet-400">Skyvern AI</div>
          </div>
          <div className="w-px h-4 bg-border/30" />
          <ArrowUpDown className="w-3 h-3 text-muted-foreground/40" />
          <div className="w-px h-4 bg-border/30" />
          {/* Data Layer */}
          <div className="flex items-center gap-2 flex-wrap justify-center">
            <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-mono text-emerald-400">Prisma ORM</div>
            <div className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[10px] font-mono text-amber-400">PostgreSQL</div>
            <div className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-[10px] font-mono text-red-400">Redis Cache</div>
          </div>
          <div className="w-px h-4 bg-border/30" />
          <ArrowUpDown className="w-3 h-3 text-muted-foreground/40" />
          <div className="w-px h-4 bg-border/30" />
          {/* Infrastructure */}
          <div className="flex items-center gap-2 flex-wrap justify-center">
            <div className="px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-[10px] font-mono text-blue-400">Vercel Edge</div>
            <div className="px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-[10px] font-mono text-blue-400">CDN</div>
            <div className="px-3 py-1.5 rounded-lg bg-orange-500/10 border border-orange-500/20 text-[10px] font-mono text-orange-400">Monitoring</div>
          </div>
        </div>
      </div>
    </div>
  );
}
