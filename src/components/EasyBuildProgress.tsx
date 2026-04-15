'use client';

import { useEffect, useRef } from 'react';
import {
  Check, Loader2, Circle, Download, PlayCircle, Sparkles, Save,
} from 'lucide-react';
import type { PhaseData } from '@/components/PipelinePhase';

/* ═══════════════════════════════════════════
   FRIENDLY PHASE LABELS (no jargon)
   ═══════════════════════════════════════════ */
const FRIENDLY_STEPS = [
  { label: 'Planning your project', detail: 'Studying what you need and how to build it' },
  { label: 'Understanding your requirements', detail: 'Making sure nothing is missed' },
  { label: 'Designing the layout', detail: 'Creating the structure and look of your app' },
  { label: 'Setting up the basics', detail: 'Preparing all the behind-the-scenes pieces' },
  { label: 'Connecting to the web', detail: 'Setting up web browsing capabilities' },
  { label: 'Building main features', detail: 'Creating the parts you\'ll use most' },
  { label: 'Checking for problems', detail: 'Making sure everything is safe and working' },
  { label: 'Adding smart features', detail: 'Connecting AI-powered tools' },
  { label: 'Adding finishing touches', detail: 'Polishing and completing extra features' },
  { label: 'Making it fast', detail: 'Optimizing speed and performance' },
  { label: 'Final quality check', detail: 'One last inspection to catch anything' },
  { label: 'Putting it online', detail: 'Deploying and getting everything live' },
];

interface EasyBuildProgressProps {
  phases: PhaseData[];
  currentPhase: number;
  confidence: number;
  isPaused: boolean;
  pipelineRunning: boolean;
  lastSaved: Date | null;
  projectName: string;
  /** Called when build is complete and user clicks "Test" */
  onTest: () => void;
  /** Called when build is complete and user clicks "Download" */
  onDownload: () => void;
}

export default function EasyBuildProgress({
  phases, currentPhase, confidence, isPaused,
  pipelineRunning, lastSaved, projectName,
  onTest, onDownload,
}: EasyBuildProgressProps) {
  const activeRef = useRef<HTMLDivElement>(null);
  const isComplete = confidence === 100 && !pipelineRunning;

  useEffect(() => {
    activeRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [currentPhase]);

  return (
    <div className="min-h-full flex items-center justify-center p-4 sm:p-8">
      <div className="w-full max-w-lg space-y-6 animate-fade-in-up">

        {/* Header */}
        <div className="text-center space-y-2">
          {isComplete ? (
            <>
              <div className="mx-auto w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-3">
                <Sparkles className="w-7 h-7 text-emerald-400" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-foreground">Your project is ready!</h1>
              <p className="text-sm text-muted-foreground">
                <span className="font-medium text-foreground">{projectName}</span> has been built, tested, and is ready to go.
              </p>
            </>
          ) : (
            <>
              <h1 className="text-xl sm:text-2xl font-bold text-foreground">
                {isPaused ? 'Build paused' : 'Building your project...'}
              </h1>
              <p className="text-sm text-muted-foreground">
                Sit back and relax — we&apos;re building <span className="font-medium text-foreground">{projectName}</span> for you.
              </p>
            </>
          )}
        </div>

        {/* Overall progress bar */}
        {!isComplete && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{isPaused ? 'Paused' : 'Working...'}</span>
              <span className="font-mono font-bold text-foreground">{confidence}%</span>
            </div>
            <div className="w-full h-3 rounded-full bg-muted/20 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 relative"
                style={{
                  width: `${confidence}%`,
                  background: 'linear-gradient(90deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190))',
                }}
              >
                {!isPaused && pipelineRunning && (
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                )}
              </div>
            </div>
          </div>
        )}

        {/* Step list */}
        <div className="space-y-1">
          {FRIENDLY_STEPS.map((friendly, i) => {
            const phase = phases[i];
            if (!phase) return null;
            const isActive = i === currentPhase && pipelineRunning;
            const isDone = phase.status === 'completed';
            const isPending = phase.status === 'pending';

            return (
              <div
                key={i}
                ref={isActive ? activeRef : undefined}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                  isActive ? 'bg-primary/8 border border-primary/20' :
                  isDone ? 'opacity-60' :
                  'opacity-30'
                }`}
              >
                {/* Status icon */}
                <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${
                  isDone ? 'bg-emerald-500/15 text-emerald-400' :
                  isActive ? 'bg-primary/15 text-primary' :
                  'bg-muted/10 text-muted-foreground/40'
                }`}>
                  {isDone ? <Check className="w-3.5 h-3.5" /> :
                   isActive ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> :
                   <Circle className="w-2.5 h-2.5" />}
                </div>

                {/* Label */}
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium truncate ${
                    isDone ? 'text-foreground/70' :
                    isActive ? 'text-foreground' :
                    'text-muted-foreground/50'
                  }`}>
                    {friendly.label}
                  </p>
                  {isActive && (
                    <p className="text-[11px] text-muted-foreground mt-0.5">{friendly.detail}</p>
                  )}
                </div>

                {/* Active step mini progress */}
                {isActive && phase.progress > 0 && (
                  <div className="w-14 flex items-center gap-1.5">
                    <div className="flex-1 h-1 rounded-full bg-muted/20 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary transition-all duration-500"
                        style={{ width: `${phase.progress}%` }}
                      />
                    </div>
                    <span className="text-[9px] font-mono text-primary">{phase.progress}%</span>
                  </div>
                )}

                {isDone && <Check className="w-3.5 h-3.5 text-emerald-400/50 flex-shrink-0" />}
              </div>
            );
          })}
        </div>

        {/* Auto-save indicator */}
        {lastSaved && !isComplete && (
          <div className="flex items-center justify-center gap-1.5 text-[10px] text-emerald-400/60">
            <Save className="w-2.5 h-2.5" /> Progress saved automatically
          </div>
        )}

        {/* Complete actions */}
        {isComplete && (
          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={onTest}
              className="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold border border-primary/30 bg-primary/10 text-primary hover:bg-primary/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <PlayCircle className="w-4 h-4" /> Test it out
            </button>
            <button
              onClick={onDownload}
              className="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-bold text-white transition-all hover:scale-[1.02] active:scale-[0.98]"
              style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190), oklch(0.55 0.18 160))' }}
            >
              <Download className="w-4 h-4" /> Download
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
