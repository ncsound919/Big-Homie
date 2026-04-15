'use client';

import { Lock, Shield, ShieldCheck, ShieldAlert, Settings } from 'lucide-react';

export type SecurityLevel = 'passive' | 'active' | 'configurable';

export interface SecuritySettingsProps {
  onSecurityLevelChange: (level: SecurityLevel) => void;
  currentLevel: SecurityLevel;
}

const LEVEL_CONFIG: Record<SecurityLevel, { 
  label: string; 
  description: string;
  icon: React.ReactNode;
  color: string;
  borderColor: string;
  bg: string;
}> = {
  passive: {
    label: 'Passive',
    description: 'Warns but doesn\'t block dangerous actions',
    icon: <ShieldAlert className="w-5 h-5" />,
    color: 'text-amber-400',
    borderColor: 'border-amber-500/30',
    bg: 'bg-amber-500/10',
  },
  active: {
    label: 'Active',
    description: 'Blocks dangerous actions automatically',
    icon: <ShieldCheck className="w-5 h-5" />,
    color: 'text-emerald-400',
    borderColor: 'border-emerald-500/30',
    bg: 'bg-emerald-500/10',
  },
  configurable: {
    label: 'Configurable',
    description: 'User can set security level per mode',
    icon: <Settings className="w-5 h-5" />,
    color: 'text-blue-400',
    borderColor: 'border-blue-500/30',
    bg: 'bg-blue-500/10',
  },
};

export default function SecuritySettings({ onSecurityLevelChange, currentLevel }: SecuritySettingsProps) {
  return (
    <div className="p-4 rounded-2xl border border-border/30 bg-background/20">
      <div className="flex items-center gap-2 mb-4">
        <Lock className="w-4 h-4 text-muted-foreground" />
        <h2 className="text-sm font-semibold text-foreground">Security Level</h2>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {(Object.keys(LEVEL_CONFIG) as SecurityLevel[]).map((level) => {
          const config = LEVEL_CONFIG[level];
          const isSelected = currentLevel === level;
          
          return (
            <button
              type="button"
              key={level}
              onClick={() => onSecurityLevelChange(level)}
              className={`p-4 rounded-xl border text-left transition-all duration-200 ${
                isSelected
                  ? `${config.borderColor} ${config.bg}`
                  : 'border-border/30 bg-background/10 hover:bg-background/20'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <div className={isSelected ? config.color : 'text-muted-foreground'}>
                  {config.icon}
                </div>
                <p className={`text-sm font-semibold ${isSelected ? config.color : 'text-foreground'}`}>
                  {config.label}
                </p>
              </div>
              <p className="text-[10px] text-muted-foreground leading-relaxed">
                {config.description}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}