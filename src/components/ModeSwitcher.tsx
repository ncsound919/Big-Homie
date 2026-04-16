'use client';

import { AppIcon } from '@/lib/icons';
import { WORKSPACE_MODES, type WorkspaceMode } from '@/lib/workspace';

interface ModeSwitcherProps {
  mode: WorkspaceMode;
  onChange: (mode: WorkspaceMode) => void;
  /** Show a pulsing indicator that a build is running in background */
  buildRunning?: boolean;
}

const modeColors: Record<WorkspaceMode, { active: string; ring: string; dot: string }> = {
  build:    { active: 'bg-purple-500/15 text-purple-400 border-purple-500/30', ring: 'ring-purple-500/20', dot: 'bg-purple-400' },
  browse:   { active: 'bg-blue-500/15 text-blue-400 border-blue-500/30', ring: 'ring-blue-500/20', dot: 'bg-blue-400' },
  research: { active: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30', ring: 'ring-cyan-500/20', dot: 'bg-cyan-400' },
  scrape:   { active: 'bg-orange-500/15 text-orange-400 border-orange-500/30', ring: 'ring-orange-500/20', dot: 'bg-orange-400' },
  ventures: { active: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30', ring: 'ring-emerald-500/20', dot: 'bg-emerald-400' },
  security: { active: 'bg-red-500/15 text-red-400 border-red-500/30', ring: 'ring-red-500/20', dot: 'bg-red-400' },
};

export default function ModeSwitcher({ mode, onChange, buildRunning }: ModeSwitcherProps) {
  return (
    <div className="flex items-center gap-0.5 rounded-lg border border-border/30 bg-background/20 p-0.5">
      {WORKSPACE_MODES.map(m => {
        const isActive = m.id === mode;
        const colors = modeColors[m.id];

        return (
          <button
            key={m.id}
            onClick={() => onChange(m.id)}
            title={m.description}
            className={`relative flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-semibold transition-all duration-200 ${
              isActive
                ? `${colors.active} border shadow-sm`
                : 'text-muted-foreground/60 hover:text-muted-foreground hover:bg-muted/10 border border-transparent'
            }`}
          >
            <AppIcon name={m.icon} className="w-3 h-3" />
            <span className="hidden sm:inline">{m.label}</span>
            {/* Build running indicator when not on build tab */}
            {m.id === 'build' && buildRunning && !isActive && (
              <span className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full ${colors.dot} animate-pulse`} />
            )}
          </button>
        );
      })}
    </div>
  );
}
