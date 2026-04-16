'use client';

import React, { useState } from 'react';
import { AppIcon } from '@/lib/icons';
import { Check, Loader2, Clock, Circle, ChevronDown, Minus } from 'lucide-react';

export interface PhaseData {
  id: number;
  name: string;
  icon: string;
  status: 'pending' | 'running' | 'completed' | 'audit';
  progress: number;
  subSteps: { name: string; status: 'pending' | 'running' | 'completed' }[];
  estimatedTime?: string;
}

interface PipelinePhaseProps {
  phase: PhaseData;
  isActive: boolean;
  isLast: boolean;
  onClick: () => void;
}

const statusIcons: Record<string, React.ReactNode> = {
  pending: <Circle className="w-3 h-3 text-muted-foreground/40" />,
  running: <Loader2 className="w-3 h-3 animate-spin text-primary" />,
  completed: <Check className="w-3 h-3 text-emerald-400" />,
  audit: <AppIcon name="shield" className="w-3 h-3 text-amber-400" />,
};

const statusGlow: Record<string, string> = {
  pending: '',
  running: 'glow-purple',
  completed: 'glow-emerald',
  audit: 'glow-cyan',
};

export default function PipelinePhase({ phase, isActive, isLast, onClick }: PipelinePhaseProps) {
  const [expanded, setExpanded] = useState(false);

  const handleClick = () => {
    setExpanded(!expanded);
    onClick();
  };

  const completedSubSteps = phase.subSteps.filter((s) => s.status === 'completed').length;
  const totalSubSteps = phase.subSteps.length;

  return (
    <div className="relative">
      <button
        onClick={handleClick}
        className={`w-full text-left p-3 sm:p-4 rounded-xl border transition-all duration-300 hover:scale-[1.005] active:scale-[0.995] ${
          isActive
            ? `border-primary/40 bg-primary/8 ${statusGlow[phase.status]}`
            : phase.status === 'completed'
            ? 'border-emerald-500/20 bg-emerald-500/5'
            : phase.status === 'audit'
            ? 'border-amber-500/20 bg-amber-500/5'
            : 'border-border/30 bg-background/20 hover:border-border/50'
        }`}
      >
        <div className="flex items-center gap-3">
          {/* Phase Number / Status */}
          <div className="relative flex-shrink-0">
            <div
              className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center text-sm font-bold transition-all duration-300 ${
                phase.status === 'completed'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : phase.status === 'running'
                  ? 'bg-primary/20 text-primary border border-primary/30 animate-pulse-glow'
                  : phase.status === 'audit'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  : 'bg-muted/30 text-muted-foreground border border-border/30'
              }`}
            >
              {phase.status === 'completed' ? (
                <Check className="w-4 h-4" />
              ) : phase.status === 'running' ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                phase.id
              )}
            </div>
          </div>

          {/* Phase Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <AppIcon name={phase.icon} className={`w-3 h-3 ${phase.status === 'completed' ? 'text-emerald-400' : phase.status === 'running' ? 'text-primary' : 'text-muted-foreground'}`} />
              <h3 className={`text-sm font-semibold truncate ${phase.status === 'completed' ? 'text-foreground' : phase.status === 'running' ? 'text-foreground' : 'text-muted-foreground'}`}>
                {phase.name}
              </h3>
              <span className="ml-auto flex-shrink-0">{statusIcons[phase.status]}</span>
            </div>

            {/* Progress Bar */}
            {phase.status !== 'pending' && (
              <div className="mt-2 flex items-center gap-2">
                <div className="flex-1 h-1 rounded-full bg-muted/30 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500 ease-out"
                    style={{
                      width: `${phase.progress}%`,
                      background: phase.status === 'completed'
                        ? 'linear-gradient(90deg, oklch(0.6 0.18 160), oklch(0.55 0.15 150))'
                        : phase.status === 'audit'
                        ? 'linear-gradient(90deg, oklch(0.65 0.18 80), oklch(0.6 0.15 70))'
                        : 'linear-gradient(90deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190))',
                    }}
                  />
                </div>
                <span className="text-[10px] font-mono text-muted-foreground w-8 text-right">
                  {Math.round(phase.progress)}%
                </span>
              </div>
            )}

            {/* Sub-step summary */}
            {phase.subSteps.length > 0 && (
              <div className="mt-1 flex items-center gap-1.5">
                <span className="text-[10px] text-muted-foreground">
                  {completedSubSteps}/{totalSubSteps} steps
                </span>
                {phase.estimatedTime && phase.status === 'running' && (
                  <>
                    <span className="text-[10px] text-muted-foreground/40">·</span>
                    <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                      <Clock className="w-2.5 h-2.5" />
                      {phase.estimatedTime}
                    </span>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Expand/Collapse chevron */}
          {phase.subSteps.length > 0 && (
            <ChevronDown className={`w-3 h-3 text-muted-foreground transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
          )}
        </div>
      </button>

      {/* Connecting line to next phase */}
      {!isLast && (
        <div className="absolute left-[1.75rem] sm:left-[2.1rem] -bottom-3 w-0.5 h-3">
          <div
            className={`h-full transition-all duration-500 ${
              phase.status === 'completed'
                ? 'bg-emerald-500/40'
                : phase.status === 'running'
                ? 'bg-primary/30'
                : 'bg-border/30'
            }`}
          />
        </div>
      )}

      {/* Expanded Sub-steps */}
      {expanded && phase.subSteps.length > 0 && (
        <div className="ml-[3.25rem] sm:ml-[3.75rem] mt-2 space-y-1 animate-fade-in-up">
          {phase.subSteps.map((step, i) => (
            <div
              key={i}
              className={`flex items-center gap-2 py-1.5 px-3 rounded-lg text-xs transition-all duration-200 ${
                step.status === 'completed'
                  ? 'text-emerald-400 bg-emerald-500/5'
                  : step.status === 'running'
                  ? 'text-primary bg-primary/5'
                  : 'text-muted-foreground/60'
              }`}
            >
              {step.status === 'completed' ? (
                <Check className="w-3 h-3 flex-shrink-0" />
              ) : step.status === 'running' ? (
                <Loader2 className="w-3 h-3 flex-shrink-0 animate-spin" />
              ) : (
                <Minus className="w-2.5 h-2.5 flex-shrink-0" />
              )}
              <span>{step.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
