'use client';

import { useState, useMemo } from 'react';
import {
  Shield, Zap, Code2, Gem, Lock, Cpu, Box,
  PieChart, Wrench, ChevronRight, ShieldCheck,
} from 'lucide-react';
import type { LucideProps } from 'lucide-react';
import type { ComponentType } from 'react';

export interface Finding {
  id: string;
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'pass';
  title: string;
  location: string;
  fixed: boolean;
  phase: number;
}

interface AuditPanelProps {
  findings: Finding[];
  auditScore: number;
  totalChecks: number;
  passedChecks: number;
}

const categoryMeta: Record<string, { icon: ComponentType<LucideProps>; color: string; label: string }> = {
  security: { icon: Shield, color: 'text-red-400', label: 'Security' },
  performance: { icon: Zap, color: 'text-orange-400', label: 'Performance' },
  typeSafety: { icon: Code2, color: 'text-blue-400', label: 'Type Safety' },
  codeQuality: { icon: Gem, color: 'text-purple-400', label: 'Code Quality' },
  raceConditions: { icon: Lock, color: 'text-yellow-400', label: 'Race Conditions' },
  memorySafety: { icon: Cpu, color: 'text-cyan-400', label: 'Memory Safety' },
  dependencies: { icon: Box, color: 'text-emerald-400', label: 'Dependencies' },
};

const severityConfig: Record<string, { color: string; bg: string; border: string; label: string }> = {
  critical: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'CRITICAL' },
  high: { color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30', label: 'HIGH' },
  medium: { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', label: 'MEDIUM' },
  low: { color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', label: 'LOW' },
  pass: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', label: 'PASS' },
};

export default function AuditPanel({ findings, auditScore, totalChecks, passedChecks }: AuditPanelProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | 'all'>('all');
  const [showPassed, setShowPassed] = useState(true);

  const categories = useMemo(() => [...new Set(findings.map(f => f.category))], [findings]);
  const filtered = useMemo(() => findings.filter(f => {
    if (selectedCategory !== 'all' && f.category !== selectedCategory) return false;
    if (!showPassed && f.severity === 'pass') return false;
    return true;
  }), [findings, selectedCategory, showPassed]);

  const criticalCount = useMemo(() => findings.filter(f => f.severity === 'critical').length, [findings]);
  const highCount = useMemo(() => findings.filter(f => f.severity === 'high').length, [findings]);
  const fixedCount = useMemo(() => findings.filter(f => f.fixed && f.severity !== 'pass').length, [findings]);

  // Group by category for summary
  const categorySummary = useMemo(() => categories.map(cat => {
    const catFindings = findings.filter(f => f.category === cat);
    const passed = catFindings.filter(f => f.severity === 'pass').length;
    const issues = catFindings.filter(f => f.severity !== 'pass').length;
    const meta = categoryMeta[cat] || { icon: Box, color: 'text-muted-foreground', label: cat };
    return { cat, passed, issues, total: catFindings.length, ...meta };
  }), [categories, findings]);

  return (
    <div className="space-y-4">
      {/* Audit Score Gauge */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="flex items-center justify-center p-4 rounded-xl border border-border/30 bg-background/20">
          <svg width="100" height="100" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="6" className="text-muted/20" />
            <circle
              cx="50" cy="50" r="40" fill="none"
              stroke={auditScore >= 90 ? '#34d399' : auditScore >= 70 ? '#fbbf24' : '#f87171'}
              strokeWidth="6" strokeLinecap="round"
              strokeDasharray={2 * Math.PI * 40}
              strokeDashoffset={2 * Math.PI * 40 - (auditScore / 100) * 2 * Math.PI * 40}
              transform="rotate(-90 50 50)"
              className="transition-all duration-1000 ease-out"
            />
            <text x="50" y="46" textAnchor="middle" dominantBaseline="central" fill="currentColor" className="text-2xl font-bold" style={{ fontSize: '22px' }}>
              {auditScore}
            </text>
            <text x="50" y="64" textAnchor="middle" fill="currentColor" className="text-muted-foreground" style={{ fontSize: '9px' }}>
              Audit Score
            </text>
          </svg>
        </div>
        <div className="p-4 rounded-xl border border-border/30 bg-background/20 flex flex-col justify-center">
          <div className="text-sm font-semibold mb-2 flex items-center gap-2">
            <PieChart className="w-3.5 h-3.5 text-primary" />
            Check Summary
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="text-center">
              <div className="text-lg font-bold text-emerald-400">{passedChecks}</div>
              <div className="text-[9px] text-muted-foreground">Passed</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-foreground">{totalChecks}</div>
              <div className="text-[9px] text-muted-foreground">Total</div>
            </div>
          </div>
        </div>
        <div className="p-4 rounded-xl border border-border/30 bg-background/20 flex flex-col justify-center">
          <div className="text-sm font-semibold mb-2 flex items-center gap-2">
            <Wrench className="w-3.5 h-3.5 text-orange-400" />
            Issues
          </div>
          <div className="grid grid-cols-3 gap-1">
            <div className="text-center">
              <div className="text-sm font-bold text-red-400">{criticalCount}</div>
              <div className="text-[8px] text-muted-foreground">Critical</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-bold text-orange-400">{highCount}</div>
              <div className="text-[8px] text-muted-foreground">High</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-bold text-emerald-400">{fixedCount}</div>
              <div className="text-[8px] text-muted-foreground">Fixed</div>
            </div>
          </div>
        </div>
      </div>

      {/* Category Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        {categorySummary.map(cs => (
          <button
            key={cs.cat}
            onClick={() => setSelectedCategory(selectedCategory === cs.cat ? 'all' : cs.cat)}
            className={`p-2.5 rounded-lg border text-center transition-all duration-200 hover:scale-105 active:scale-95 ${
              selectedCategory === cs.cat
                ? 'border-primary/40 bg-primary/10'
                : 'border-border/30 bg-background/20 hover:border-border/50'
            }`}
          >
            <cs.icon className={`w-4 h-4 mx-auto ${cs.color} mb-1`} />
            <div className="text-[9px] text-muted-foreground font-medium">{cs.label}</div>
            <div className="text-[10px] font-mono mt-0.5">
              <span className="text-emerald-400">{cs.passed}</span>
              <span className="text-muted-foreground/40">/</span>
              <span className="text-foreground/70">{cs.total}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setSelectedCategory('all')}
          className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-all ${
            selectedCategory === 'all' ? 'bg-primary/20 text-primary border border-primary/30' : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          All Categories
        </button>
        <label className="flex items-center gap-1.5 text-[10px] text-muted-foreground cursor-pointer">
          <input
            type="checkbox"
            checked={showPassed}
            onChange={(e) => setShowPassed(e.target.checked)}
            className="accent-primary w-3 h-3"
          />
          Show passed
        </label>
      </div>

      {/* Findings List */}
      <div className="space-y-1.5 max-h-[300px] overflow-y-auto">
        {filtered.map(finding => {
          const sev = severityConfig[finding.severity];
          const cat = categoryMeta[finding.category] || categoryMeta.security;
          return (
            <div
              key={finding.id}
              className={`p-2.5 rounded-lg border-l-[3px] ${sev.bg} ${sev.border} transition-all duration-200 hover:translate-x-1`}
              style={{ borderLeftColor: finding.severity === 'critical' ? '#f87171' : finding.severity === 'high' ? '#fb923c' : finding.severity === 'medium' ? '#fbbf24' : finding.severity === 'low' ? '#22d3ee' : '#34d399' }}
            >
              <div className="flex items-start gap-2">
                <cat.icon className={`w-3 h-3 ${cat.color} mt-0.5 flex-shrink-0`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-medium text-foreground">{finding.title}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${sev.bg} ${sev.color} border ${sev.border}`}>
                      {sev.label}
                    </span>
                    {finding.fixed && (
                      <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        FIXED
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-muted-foreground font-mono mt-0.5">{finding.location}</div>
                </div>
              </div>
            </div>
          );
        })}
        {filtered.length === 0 && (
          <div className="py-8 text-center text-xs text-muted-foreground/50">
            <ShieldCheck className="w-5 h-5 mx-auto mb-1" />
            No findings match your filter
          </div>
        )}
      </div>
    </div>
  );
}
