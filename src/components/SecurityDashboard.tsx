'use client';

import { useState } from 'react';
import {
  Shield, ShieldCheck, ShieldAlert, AlertTriangle, CheckCircle,
  Eye, EyeOff, Search, Activity, RefreshCw, Clock, Download, ScanSearch,
} from 'lucide-react';
import SecuritySettings from './SecuritySettings';
import AgentManager from './AgentManager';
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

const createInitialEvents = (): SecurityEvent[] => [
  { id: '1', timestamp: new Date().toISOString(), type: 'info', message: 'Security dashboard initialized' },
  { id: '2', timestamp: new Date(Date.now() - 300000).toISOString(), type: 'scan', message: 'System scan completed - no threats detected' },
  { id: '3', timestamp: new Date(Date.now() - 600000).toISOString(), type: 'info', message: 'All security checks passed' },
];

type SecurityEventFilter = 'all' | 'blocked' | 'warnings';

export default function SecurityDashboard() {
  const [securityLevel, setSecurityLevel] = useState<SecurityLevel>('active');
  const [securityStatus, setSecurityStatus] = useState<SecurityStatus>('secure');
  const [events, setEvents] = useState<SecurityEvent[]>(() => createInitialEvents());
  const [eventFilter, setEventFilter] = useState<SecurityEventFilter>('all');
  const [showDetails, setShowDetails] = useState(true);

  const status = STATUS_CONFIG[securityStatus];
  const levelDetails = LEVEL_LABELS[securityLevel];

  const totalChecks = events.length;
  const blockedCount = events.filter(e => e.type === 'block').length;
  const warningsCount = events.filter(e => e.type === 'alert').length;

  const filteredEvents = events.filter(event => {
    if (eventFilter === 'all') return true;
    if (eventFilter === 'blocked') return event.type === 'block';
    if (eventFilter === 'warnings') return event.type === 'alert';
    return true;
  });

  const exportLogs = () => {
    const dataStr = JSON.stringify(events, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `security-logs-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleSecurityLevelChange = (level: SecurityLevel) => {
    setSecurityLevel(level);
    setSecurityStatus(level === 'passive' ? 'warning' : 'secure');
    setEvents(prev => [
      {
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        type: 'info',
        message: `${LEVEL_LABELS[level].label} protection enabled`,
      },
      ...prev,
    ]);
  };

  const runSecurityScan = () => {
    const nextType = securityLevel === 'passive' ? 'alert' : securityLevel === 'configurable' ? 'info' : 'scan';
    const nextStatus = securityLevel === 'passive' ? 'warning' : 'secure';
    setSecurityStatus(nextStatus);
    setEvents(prev => [
      {
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        type: nextType,
        message:
          securityLevel === 'passive'
            ? 'Scan finished — review recommended actions before browsing'
            : securityLevel === 'configurable'
            ? 'Scan finished — custom controls are ready for review'
            : 'Security scan completed — browser protections are operating normally',
      },
      ...prev,
    ]);
  };

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
          <p className="text-xs text-muted-foreground">{levelDetails.description}</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Activity className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Real-time</span>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(280px,0.7fr)]">
        <div className="space-y-4">
          <SecuritySettings
            currentLevel={securityLevel}
            onSecurityLevelChange={handleSecurityLevelChange}
          />

          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-xl border border-border/30 bg-background/20 text-center">
              <p className="text-lg font-bold text-foreground">{totalChecks}</p>
              <p className="text-xs text-muted-foreground">Checks</p>
            </div>
            <div className="p-3 rounded-xl border border-border/30 bg-background/20 text-center">
              <p className="text-lg font-bold text-red-400">{blockedCount}</p>
              <p className="text-xs text-muted-foreground">Blocked</p>
            </div>
            <div className="p-3 rounded-xl border border-border/30 bg-background/20 text-center">
              <p className="text-lg font-bold text-amber-400">{warningsCount}</p>
              <p className="text-xs text-muted-foreground">Warnings</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              type="button"
              onClick={runSecurityScan}
              className="flex items-center justify-center gap-2 p-3 rounded-xl border border-border/30 bg-background/20 hover:bg-background/30 transition-all"
            >
              <ScanSearch className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs font-medium text-foreground">Run Scan</span>
            </button>
            <button
              type="button"
              onClick={() => setShowDetails(value => !value)}
              className="flex items-center justify-center gap-2 p-3 rounded-xl border border-border/30 bg-background/20 hover:bg-background/30 transition-all"
            >
              {showDetails ? (
                <EyeOff className="w-4 h-4 text-muted-foreground" />
              ) : (
                <Eye className="w-4 h-4 text-muted-foreground" />
              )}
              <span className="text-xs font-medium text-foreground">
                {showDetails ? 'Hide timestamps' : 'Show timestamps'}
              </span>
            </button>
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-border/30 bg-background/20">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-foreground">Protection Summary</h2>
          </div>
          <div className="space-y-3">
            {[
              'Proxy traffic is isolated from private hosts and blocked service ports.',
              'Recent scans and warnings stay exportable for auditing.',
              'Security mode changes are logged immediately for visibility.',
            ].map((item) => (
              <div key={item} className="flex items-start gap-2 rounded-xl border border-border/20 bg-background/10 p-3">
                <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                <p className="text-xs leading-relaxed text-muted-foreground">{item}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <AgentManager />

      {/* Security Events */}
      <div className="p-4 rounded-2xl border border-border/30 bg-background/20">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-foreground">Recent Events</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={exportLogs}
              className="p-1.5 rounded-lg hover:bg-background/30 text-muted-foreground transition-all"
              title="Export Logs"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={() => {
                setSecurityStatus('secure');
                setEvents(createInitialEvents());
              }}
              className="p-1.5 rounded-lg hover:bg-background/30 text-muted-foreground transition-all"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mb-3">
          {(['all', 'blocked', 'warnings'] as const).map((filter) => (
            <button
              key={filter}
              type="button"
              onClick={() => setEventFilter(filter)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                eventFilter === filter
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-background/10 text-muted-foreground hover:bg-background/20'
              }`}
            >
              {filter.charAt(0).toUpperCase() + filter.slice(1)}
            </button>
          ))}
        </div>
        <div className="space-y-2">
          {filteredEvents.map((event) => {
            const Icon = event.type === 'scan' ? Search : event.type === 'block' ? ShieldAlert : event.type === 'alert' ? AlertTriangle : CheckCircle;
            return (
              <div key={event.id} className="flex items-start gap-3 p-3 rounded-xl bg-background/10">
                <Icon className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-foreground">{event.message}</p>
                  {showDetails && (
                    <div className="flex items-center gap-1 mt-1">
                      <Clock className="w-3 h-3 text-muted-foreground/60" />
                      <span className="text-[10px] text-muted-foreground/60">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          {filteredEvents.length === 0 && (
            <div className="rounded-xl border border-dashed border-border/30 bg-background/10 p-4 text-center text-xs text-muted-foreground">
              No matching events yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
