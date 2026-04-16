'use client';

import { useState } from 'react';
import {
  Brain, ChevronRight, Network, ListChecks, TriangleAlert, Boxes,
  Workflow, Gauge, Clock, Loader2, Play,
} from 'lucide-react';

export interface AIAnalysis {
  summary: string;
  architecture: {
    frontend: string;
    backend: string;
    database: string;
    infrastructure: string;
  };
  features: string[];
  risks: { name: string; severity: string; mitigation: string }[];
  estimatedComplexity: string;
  suggestedTimeline: string;
  techStack: string[];
  keyComponents: string[];
}

interface AIAnalysisCardProps {
  analysis: AIAnalysis;
  onStart: () => void;
  isStarting: boolean;
}

const severityColors: Record<string, string> = {
  high: 'text-red-400 bg-red-500/10 border-red-500/30',
  medium: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  low: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
};

const complexityColors: Record<string, string> = {
  low: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  medium: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  high: 'text-red-400 bg-red-500/10 border-red-500/30',
};

export default function AIAnalysisCard({ analysis, onStart, isStarting }: AIAnalysisCardProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    architecture: true,
    features: true,
    risks: false,
    techStack: true,
  });

  const toggle = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  return (
    <div className="w-full max-w-2xl mx-auto animate-fade-in-up">
      <div className="glass-strong rounded-2xl p-6 sm:p-8 gradient-border">
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-medium mb-3">
            <Brain className="w-3 h-3 animate-pulse" />
            AI Analysis Complete
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-foreground">
            Project Blueprint
          </h2>
        </div>

        {/* Summary */}
        <div className="mb-4 p-3 rounded-xl bg-background/50 border border-border/30">
          <p className="text-sm text-foreground/90 leading-relaxed">{analysis.summary}</p>
          <div className="flex items-center gap-3 mt-3">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium border ${complexityColors[analysis.estimatedComplexity] || complexityColors.medium}`}>
              <Gauge className="w-3 h-3" />
              {analysis.estimatedComplexity.charAt(0).toUpperCase() + analysis.estimatedComplexity.slice(1)} Complexity
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium text-cyan-400 bg-cyan-500/10 border border-cyan-500/30">
              <Clock className="w-3 h-3" />
              {analysis.suggestedTimeline}
            </span>
          </div>
        </div>

        {/* Architecture */}
        <div className="mb-3">
          <button
            onClick={() => toggle('architecture')}
            className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors w-full"
          >
            <ChevronRight className={`w-3 h-3 transition-transform duration-200 ${expandedSections.architecture ? 'rotate-90' : ''}`} />
            <Network className="w-3.5 h-3.5 text-purple-400" />
            Architecture
          </button>
          {expandedSections.architecture && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 ml-5 animate-fade-in-up">
              {Object.entries(analysis.architecture).map(([key, value]) => (
                <div key={key} className="p-2.5 rounded-lg bg-background/30 border border-border/20">
                  <p className="text-xs text-muted-foreground capitalize mb-0.5">{key}</p>
                  <p className="text-xs text-foreground font-medium">{value}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Features */}
        <div className="mb-3">
          <button
            onClick={() => toggle('features')}
            className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors w-full"
          >
            <ChevronRight className={`w-3 h-3 transition-transform duration-200 ${expandedSections.features ? 'rotate-90' : ''}`} />
            <ListChecks className="w-3.5 h-3.5 text-cyan-400" />
            Key Features
            <span className="text-xs text-muted-foreground">({analysis.features.length})</span>
          </button>
          {expandedSections.features && (
            <div className="flex flex-wrap gap-1.5 mt-2 ml-5 animate-fade-in-up">
              {analysis.features.map((f, i) => (
                <span key={i} className="px-2.5 py-1 rounded-md text-xs bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  {f}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Risks */}
        <div className="mb-3">
          <button
            onClick={() => toggle('risks')}
            className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors w-full"
          >
            <ChevronRight className={`w-3 h-3 transition-transform duration-200 ${expandedSections.risks ? 'rotate-90' : ''}`} />
            <TriangleAlert className="w-3.5 h-3.5 text-amber-400" />
            Identified Risks
            <span className="text-xs text-muted-foreground">({analysis.risks.length})</span>
          </button>
          {expandedSections.risks && (
            <div className="space-y-1.5 mt-2 ml-5 animate-fade-in-up">
              {analysis.risks.map((risk, i) => (
                <div key={i} className="p-2.5 rounded-lg bg-background/30 border border-border/20">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-xs text-foreground">{risk.name}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${severityColors[risk.severity] || severityColors.medium}`}>
                      {risk.severity}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">{risk.mitigation}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tech Stack */}
        <div className="mb-3">
          <button
            onClick={() => toggle('techStack')}
            className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors w-full"
          >
            <ChevronRight className={`w-3 h-3 transition-transform duration-200 ${expandedSections.techStack ? 'rotate-90' : ''}`} />
            <Boxes className="w-3.5 h-3.5 text-emerald-400" />
            Tech Stack
          </button>
          {expandedSections.techStack && (
            <div className="flex flex-wrap gap-1.5 mt-2 ml-5 animate-fade-in-up">
              {analysis.techStack.map((tech, i) => (
                <span key={i} className="px-2.5 py-1 rounded-md text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  {tech}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Key Components */}
        <div className="mb-5">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground mb-2">
            <Workflow className="w-3.5 h-3.5 text-purple-400" />
            Key Components
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 ml-5">
            {analysis.keyComponents.map((comp, i) => (
              <div key={i} className="px-2.5 py-1.5 rounded-lg bg-background/30 border border-border/20 text-xs text-foreground/80 text-center">
                {comp}
              </div>
            ))}
          </div>
        </div>

        {/* Start Build Button */}
        <button
          onClick={onStart}
          disabled={isStarting}
          className="w-full py-3 px-6 rounded-xl font-semibold text-sm transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
          style={{
            background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190), oklch(0.55 0.18 160))',
            color: 'white',
          }}
        >
          {isStarting ? (
            <span className="flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Initializing Build Pipeline...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <Play className="w-4 h-4" />
              Start Autonomous Build
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
