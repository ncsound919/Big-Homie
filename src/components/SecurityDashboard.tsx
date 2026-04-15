'use client';

import { useState } from 'react';
import {
  Shield, ShieldCheck, ShieldAlert, AlertTriangle, CheckCircle,
  Eye, EyeOff, Search, Activity, RefreshCw, Clock,
} from 'lucide-react';
import SecuritySettings from './SecuritySettings';
import type { SecurityLevel } from './SecuritySettings';
type SecurityStatus = 'secure' | 'warning' | 'critical';

interface SecurityEvent {
  id: string;
  timestamp: string;
  type: 'scan' | 'block' | 'alert' | 'info';
  message: string;
}

const STATUS_CONFIG: Record<SecurityStatus, { color: string; bg: string; icon: React.ReactNode; label: string }> = {
  secure: {
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10 border-emerald-500/20',
    icon: <ShieldCheck className="w-5 h-5" />,
    label: 'Secure',
  },
  warning: {
    color: 'text-amber-400',
    bg: 'bg-amber-500/10 border-amber-500/20',
    icon: <AlertTriangle className="w-5 h-5" />,
    label: 'Warning',
  },
  critical: {
    color: 'text-red-400',
    bg: 'bg-red-500/10 border-red-500/20',
    icon: <ShieldAlert className="w-5 h-5" />,
    label: 'Critical',
  },
};

const LEVEL_LABELS: Record<SecurityLevel, { label: string; description: string }> = {
  passive: { label: 'Passive', description: 'Monitors and logs activities only' },
  active: { label: 'Active', description: 'Blocks suspicious activities automatically' },
  configurable: { label: 'Configurable', description: 'User-controlled security policies' },
};

const INITIAL_EVENTS: SecurityEvent[] = [
  { id: '1', timestamp: new Date().toISOString(), type: 'info', message: 'Security dashboard initialized' },
  { id: '2', timestamp: new Date(Date.now() - 300000).toISOString(), type: 'scan', message: 'System scan completed - no threats detected' },
  { id: '3', timestamp: new Date(Date.now() - 600000).toISOString(), type: 'info', message: 'All security checks passed' },
];

export default function SecurityDashboard() {
  const [securityLevel, setSecurityLevel] = useState<SecurityLevel>('active');
  const [securityStatus, setSecurityStatus] = useState<SecurityStatus>('secure');
  const [events, setEvents] = useState<SecurityEvent[]>(INITIAL_EVENTS);

  const status = STATUS_CONFIG[securityStatus];

  return (
    <div className="min-h-full p-4 sm:p-6 lg:p-8 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center bg-gradient-to-br from-red-500/20 to-red-600/5">
          <Shield className="w-6 h-6 text-red-400" />
        </div>
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-foreground">Security Dashboard</h1>
          <p className="text-xs sm:text-sm text-muted-foreground">Monitor and protect your workspace</p>
        </div>
      </div>

      {/* Status Card */}
      <div className={`flex items-center gap-4 p-4 rounded-2xl border ${status.bg}`}>
        <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${status.bg}`}>
          {status.icon}
        </div>
        <div className="flex-1">
          <p className={`text-lg font-bold ${status.color}`}>{status.label}</p>
          <p className="text-xs text-muted-foreground">All systems operational</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Activity className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Real-time</span>
        </div>
      </div>

      {/* Security Settings */}
      <SecuritySettings
        currentLevel={securityLevel}
        onSecurityLevelChange={setSecurityLevel}
      />

      {/* Security Events */}
      <div className="p-4 rounded-2xl border border-border/30 bg-background/20">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-foreground">Recent Events</h2>
          </div>
          <button className="p-1.5 rounded-lg hover:bg-background/30 text-muted-foreground transition-all">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="space-y-2">
          {events.map((event) => {
            const Icon = event.type === 'scan' ? Search : event.type === 'block' ? ShieldAlert : event.type === 'alert' ? AlertTriangle : CheckCircle;
            return (
              <div key={event.id} className="flex items-start gap-3 p-3 rounded-xl bg-background/10">
                <Icon className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-foreground truncate">{event.message}</p>
                  <div className="flex items-center gap-1 mt-1">
                    <Clock className="w-3 h-3 text-muted-foreground/60" />
                    <span className="text-[10px] text-muted-foreground/60">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3">
        <button className="flex items-center justify-center gap-2 p-3 rounded-xl border border-border/30 bg-background/20 hover:bg-background/30 transition-all">
          <Eye className="w-4 h-4 text-muted-foreground" />
          <span className="text-xs font-medium text-foreground">Scan Now</span>
        </button>
        <button className="flex items-center justify-center gap-2 p-3 rounded-xl border border-border/30 bg-background/20 hover:bg-background/30 transition-all">
          <EyeOff className="w-4 h-4 text-muted-foreground" />
          <span className="text-xs font-medium text-foreground">Hide Details</span>
        </button>
      </div>
    </div>
  );
}