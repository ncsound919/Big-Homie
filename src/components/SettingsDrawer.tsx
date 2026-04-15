'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import type { ReactNode, ChangeEvent } from 'react';
import {
  X, Eye, EyeOff, Settings2, Zap, Brain, Upload, Plug, KeyRound,
  CheckCircle2, AlertCircle, Loader2, Trash2, ExternalLink, ToggleLeft, ToggleRight,
  Sparkles, Code2, Monitor, Cpu, ChevronRight, Power, Bot, FileUp, Info,
} from 'lucide-react';
import {
  getSettings, saveSettings, DEFAULT_INTEGRATIONS,
  type AppSettings, type AppMode, type LocalModelConfig, type CustomAgent, type IntegrationConfig,
} from '@/lib/settings';
import {
  getCredentials, saveCredentials, clearCredentials, type Credentials,
} from '@/lib/credentials';

/* ─── Shared sub-components ─── */

function MaskedInput({ label, value, onChange, placeholder, helpText, hint, mono = true }: {
  label: string; value: string; onChange: (v: string) => void;
  placeholder?: string; helpText?: string; hint?: ReactNode; mono?: boolean;
}) {
  const [show, setShow] = useState(false);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-2">
        <label className="text-xs font-medium text-foreground">{label}</label>
        {hint}
      </div>
      <div className="relative">
        <input
          type={show ? 'text' : 'password'}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete="off"
          spellCheck={false}
          className={`w-full pr-9 pl-3 py-2 text-xs rounded-lg border border-border/30 bg-background/40 text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-primary/40 ${mono ? 'font-mono' : ''}`}
        />
        <button type="button" onClick={() => setShow(v => !v)} tabIndex={-1}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-foreground transition-colors">
          {show ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
        </button>
      </div>
      {helpText && <p className="text-[10px] text-muted-foreground/60">{helpText}</p>}
    </div>
  );
}

function Toggle({ on, onToggle, label, description }: {
  on: boolean; onToggle: () => void; label: string; description?: string;
}) {
  return (
    <button type="button" onClick={onToggle}
      className="w-full flex items-center gap-3 p-3 rounded-xl border border-border/20 bg-background/20 hover:bg-background/40 transition-all text-left group">
      {on
        ? <ToggleRight className="w-5 h-5 text-primary flex-shrink-0" />
        : <ToggleLeft className="w-5 h-5 text-muted-foreground/40 flex-shrink-0" />}
      <div className="flex-1 min-w-0">
        <span className="text-xs font-medium text-foreground">{label}</span>
        {description && <p className="text-[10px] text-muted-foreground mt-0.5">{description}</p>}
      </div>
    </button>
  );
}

function SectionHeader({ icon: Icon, title, badge }: {
  icon: typeof Settings2; title: string; badge?: ReactNode;
}) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <Icon className="w-4 h-4 text-primary" />
      <h3 className="text-xs font-bold text-foreground uppercase tracking-wider">{title}</h3>
      {badge}
    </div>
  );
}

/* ─── Tabs ─── */
type Tab = 'general' | 'models' | 'agents' | 'integrations' | 'credentials';

const TABS: { id: Tab; label: string; icon: typeof Settings2 }[] = [
  { id: 'general', label: 'General', icon: Settings2 },
  { id: 'models', label: 'Models', icon: Brain },
  { id: 'agents', label: 'Agents', icon: Bot },
  { id: 'integrations', label: 'Integrations', icon: Plug },
  { id: 'credentials', label: 'Credentials', icon: KeyRound },
];

/* ─── Integration Category Groups ─── */
const INTEGRATION_GROUPS: { label: string; ids: string[] }[] = [
  { label: 'CI/CD & Hosting', ids: ['vercel', 'netlify', 'railway'] },
  { label: 'Database', ids: ['supabase', 'neon', 'planetscale', 'turso'] },
  { label: 'AI / LLM', ids: ['openai', 'anthropic', 'groq'] },
  { label: 'Monitoring', ids: ['sentry', 'posthog'] },
  { label: 'Auth', ids: ['clerk', 'auth0'] },
  { label: 'Payments', ids: ['stripe', 'lemonsqueezy'] },
  { label: 'Email', ids: ['resend', 'sendgrid'] },
  { label: 'Storage', ids: ['cloudflare-r2', 'uploadthing'] },
];

/* ═══════════════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════════════ */

interface SettingsDrawerProps {
  open: boolean;
  onClose: () => void;
}

export default function SettingsDrawer({ open, onClose }: SettingsDrawerProps) {
  const [tab, setTab] = useState<Tab>('general');
  const [settings, setSettings] = useState<AppSettings>(getSettings);
  const [creds, setCreds] = useState<Credentials>(getCredentials);
  const [ghStatus, setGhStatus] = useState<'idle' | 'testing' | 'valid' | 'invalid'>('idle');
  const [ghUser, setGhUser] = useState('');
  const [dirty, setDirty] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const hydrateTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (open) {
      hydrateTimerRef.current = setTimeout(() => {
        setSettings(getSettings());
        setCreds(getCredentials());
        setGhStatus('idle');
        setGhUser('');
        setDirty(false);
      }, 0);
    }

    return () => {
      if (hydrateTimerRef.current) {
        clearTimeout(hydrateTimerRef.current);
        hydrateTimerRef.current = null;
      }
    };
  }, [open]);

  const update = useCallback(<K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setDirty(true);
  }, []);

  const updateNested = useCallback(<K extends keyof AppSettings>(
    key: K, partial: Partial<AppSettings[K]>,
  ) => {
    setSettings(prev => ({ ...prev, [key]: { ...(prev[key] as object), ...partial } as AppSettings[K] }));
    setDirty(true);
  }, []);

  const updateIntegration = useCallback((id: string, partial: Partial<IntegrationConfig>) => {
    setSettings(prev => ({
      ...prev,
      integrations: prev.integrations.map(i => i.id === id ? { ...i, ...partial } : i),
    }));
    setDirty(true);
  }, []);

  const handleSave = () => {
    saveSettings(settings);
    saveCredentials({
      githubToken: creds.githubToken.trim(),
      vercelToken: creds.vercelToken.trim(),
      supabaseUrl: creds.supabaseUrl.trim(),
      supabaseKey: creds.supabaseKey.trim(),
    });
    setDirty(false);
  };

  /* ─── GitHub test ─── */
  const testGitHub = async () => {
    if (!creds.githubToken.trim()) return;
    setGhStatus('testing');
    try {
      const res = await fetch('/api/github?action=user', {
        headers: { Authorization: `Bearer ${creds.githubToken.trim()}` },
      });
      if (res.ok) {
        const data = await res.json() as { login?: string };
        setGhUser(data.login ?? '');
        setGhStatus('valid');
      } else {
        setGhStatus('invalid'); setGhUser('');
      }
    } catch {
      setGhStatus('invalid'); setGhUser('');
    }
  };

  /* ─── Agent upload ─── */
  const handleAgentUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const maxSize = 512 * 1024; // 512KB limit
    if (file.size > maxSize) {
      alert('Agent config must be under 512KB');
      return;
    }
    const allowedExts = ['.json', '.yaml', '.yml', '.md', '.txt', '.toml'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedExts.includes(ext)) {
      alert(`Unsupported file type. Allowed: ${allowedExts.join(', ')}`);
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const content = reader.result as string;
      const agent: CustomAgent = {
        id: crypto.randomUUID(),
        name: file.name.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' '),
        description: '',
        config: content,
        fileName: file.name,
        enabled: true,
        addedAt: new Date().toISOString(),
      };
      update('customAgents', [...settings.customAgents, agent]);
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  const removeAgent = (id: string) => {
    update('customAgents', settings.customAgents.filter(a => a.id !== id));
  };

  const toggleAgent = (id: string) => {
    update('customAgents', settings.customAgents.map(a =>
      a.id === id ? { ...a, enabled: !a.enabled } : a
    ));
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Drawer */}
      <div className="relative w-full max-w-xl h-full border-l border-border/30 bg-background shadow-2xl overflow-hidden animate-slide-in-right z-10 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border/20 flex-shrink-0">
          <div className="flex items-center gap-2">
            <Settings2 className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-bold">Settings</h2>
            {settings.mode === 'dev' && (
              <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-orange-500/10 text-orange-400 border border-orange-500/20">
                DEV MODE
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {dirty && (
              <span className="text-[10px] text-amber-400 font-medium">Unsaved changes</span>
            )}
            <button onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-background/60 text-muted-foreground hover:text-foreground transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border/20 px-3 overflow-x-auto flex-shrink-0">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-3 py-2.5 text-[11px] font-medium border-b-2 transition-all whitespace-nowrap ${
                tab === t.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}>
              <t.icon className="w-3 h-3" />
              {t.label}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-6">
          {/* ══════ GENERAL TAB ══════ */}
          {tab === 'general' && (
            <>
              {/* Mode Selector */}
              <div>
                <SectionHeader icon={Sparkles} title="Experience Mode" />
                <div className="grid grid-cols-2 gap-3">
                  {([
                    { id: 'easy' as const, label: 'Easy Mode', icon: Sparkles, color: 'text-emerald-400',
                      desc: 'Simplified interface with smart defaults. Perfect for quick projects.' },
                    { id: 'dev' as const, label: 'Dev Mode', icon: Code2, color: 'text-orange-400',
                      desc: 'Full control over every pipeline phase, integration, and agent.' },
                  ]).map(m => (
                    <button key={m.id} type="button"
                      onClick={() => update('mode', m.id)}
                      className={`p-4 rounded-xl border text-left transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] ${
                        settings.mode === m.id
                          ? 'border-primary/50 bg-primary/10 glow-purple'
                          : 'border-border/30 bg-background/20 hover:border-primary/30'
                      }`}>
                      <m.icon className={`w-5 h-5 ${m.color} mb-2`} />
                      <p className="text-xs font-semibold text-foreground">{m.label}</p>
                      <p className="text-[10px] text-muted-foreground mt-1 leading-snug">{m.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Pipeline Settings */}
              <div>
                <SectionHeader icon={Zap} title="Pipeline" />
                <div className="space-y-2">
                  <Toggle on={settings.pipeline.autoFix} label="Auto-fix issues"
                    description="Automatically resolve audit findings during build"
                    onToggle={() => updateNested('pipeline', { autoFix: !settings.pipeline.autoFix })} />
                  {settings.mode === 'dev' && (
                    <>
                      <Toggle on={settings.pipeline.skipAudit} label="Skip audit gates"
                        description="Bypass quality gates for faster iteration (not recommended)"
                        onToggle={() => updateNested('pipeline', { skipAudit: !settings.pipeline.skipAudit })} />
                      <Toggle on={settings.pipeline.parallelPhases} label="Parallel phases"
                        description="Run non-dependent phases concurrently"
                        onToggle={() => updateNested('pipeline', { parallelPhases: !settings.pipeline.parallelPhases })} />
                    </>
                  )}
                  <div className="p-3 rounded-xl border border-border/20 bg-background/20">
                    <label className="text-xs font-medium text-foreground mb-2 block">Default Speed</label>
                    <div className="flex gap-2">
                      {[0.5, 1, 2, 5].map(s => (
                        <button key={s} type="button"
                          onClick={() => updateNested('pipeline', { defaultSpeed: s })}
                          className={`flex-1 px-2 py-1.5 rounded-lg text-[11px] font-bold transition-all ${
                            settings.pipeline.defaultSpeed === s
                              ? 'bg-primary/20 text-primary border border-primary/30'
                              : 'bg-muted/20 text-muted-foreground border border-border/20 hover:text-foreground'
                          }`}>
                          {s}x
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* UI Settings */}
              <div>
                <SectionHeader icon={Monitor} title="Interface" />
                <div className="space-y-2">
                  <Toggle on={settings.ui.particles} label="Particle background"
                    description="Animated particles behind the UI"
                    onToggle={() => updateNested('ui', { particles: !settings.ui.particles })} />
                  <Toggle on={settings.ui.animations} label="Animations"
                    description="Transition and entrance animations"
                    onToggle={() => updateNested('ui', { animations: !settings.ui.animations })} />
                  <Toggle on={settings.ui.compactView} label="Compact view"
                    description="Reduce spacing for more content on screen"
                    onToggle={() => updateNested('ui', { compactView: !settings.ui.compactView })} />
                  {settings.mode === 'dev' && (
                    <Toggle on={settings.ui.showTechDetails} label="Show tech details"
                      description="Display raw data, phase timing, and debug info"
                      onToggle={() => updateNested('ui', { showTechDetails: !settings.ui.showTechDetails })} />
                  )}
                </div>
              </div>
            </>
          )}

          {/* ══════ MODELS TAB ══════ */}
          {tab === 'models' && (
            <>
              <div>
                <SectionHeader icon={Brain} title="AI Model Provider" />
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <button type="button"
                    onClick={() => update('modelProvider', 'cloud')}
                    className={`p-4 rounded-xl border text-left transition-all hover:scale-[1.02] active:scale-[0.98] ${
                      settings.modelProvider === 'cloud'
                        ? 'border-primary/50 bg-primary/10 glow-purple'
                        : 'border-border/30 bg-background/20 hover:border-primary/30'
                    }`}>
                    <Sparkles className="w-5 h-5 text-purple-400 mb-2" />
                    <p className="text-xs font-semibold">Cloud AI</p>
                    <p className="text-[10px] text-muted-foreground mt-1">Use hosted APIs (OpenAI, Anthropic, Groq)</p>
                  </button>
                  <button type="button"
                    onClick={() => update('modelProvider', 'local')}
                    className={`p-4 rounded-xl border text-left transition-all hover:scale-[1.02] active:scale-[0.98] ${
                      settings.modelProvider === 'local'
                        ? 'border-primary/50 bg-primary/10 glow-purple'
                        : 'border-border/30 bg-background/20 hover:border-primary/30'
                    }`}>
                    <Cpu className="w-5 h-5 text-orange-400 mb-2" />
                    <p className="text-xs font-semibold">Local Model</p>
                    <p className="text-[10px] text-muted-foreground mt-1">Ollama, LM Studio, or llama.cpp</p>
                  </button>
                </div>
              </div>

              {settings.modelProvider === 'local' && (
                <div className="space-y-4 p-4 rounded-xl border border-orange-500/20 bg-orange-500/5">
                  <SectionHeader icon={Cpu} title="Local Model Configuration" />

                  {/* Provider select */}
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">Runtime</label>
                    <div className="grid grid-cols-4 gap-2">
                      {(['ollama', 'lmstudio', 'llamacpp', 'custom'] as const).map(p => (
                        <button key={p} type="button"
                          onClick={() => updateNested('localModel', { provider: p })}
                          className={`px-2 py-1.5 rounded-lg text-[10px] font-medium transition-all ${
                            settings.localModel.provider === p
                              ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                              : 'bg-muted/20 text-muted-foreground border border-border/20 hover:text-foreground'
                          }`}>
                          {p === 'ollama' ? 'Ollama' : p === 'lmstudio' ? 'LM Studio' : p === 'llamacpp' ? 'llama.cpp' : 'Custom'}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Endpoint */}
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">API Endpoint</label>
                    <input
                      type="url"
                      value={settings.localModel.endpoint}
                      onChange={e => updateNested('localModel', { endpoint: e.target.value })}
                      placeholder={settings.localModel.provider === 'ollama' ? 'http://localhost:11434' : 'http://localhost:1234/v1'}
                      className="w-full px-3 py-2 text-xs rounded-lg border border-border/30 bg-background/40 font-mono focus:outline-none focus:border-primary/40"
                    />
                    <p className="text-[10px] text-muted-foreground/60">
                      {settings.localModel.provider === 'ollama' && 'Default: http://localhost:11434'}
                      {settings.localModel.provider === 'lmstudio' && 'Default: http://localhost:1234/v1'}
                      {settings.localModel.provider === 'llamacpp' && 'Default: http://localhost:8080/v1'}
                      {settings.localModel.provider === 'custom' && 'Any OpenAI-compatible endpoint'}
                    </p>
                  </div>

                  {/* Model name */}
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">Model Name</label>
                    <input
                      type="text"
                      value={settings.localModel.modelName}
                      onChange={e => updateNested('localModel', { modelName: e.target.value })}
                      placeholder="llama3.1"
                      className="w-full px-3 py-2 text-xs rounded-lg border border-border/30 bg-background/40 font-mono focus:outline-none focus:border-primary/40"
                    />
                  </div>

                  {/* API Key (for custom endpoints) */}
                  {settings.localModel.provider === 'custom' && (
                    <MaskedInput
                      label="API Key"
                      value={settings.localModel.apiKey}
                      onChange={v => updateNested('localModel', { apiKey: v })}
                      placeholder="sk-..."
                      helpText="Only needed for authenticated custom endpoints"
                    />
                  )}

                  <div className="flex items-start gap-2 p-2.5 rounded-lg bg-blue-500/5 border border-blue-500/20">
                    <Info className="w-3.5 h-3.5 text-blue-400 mt-0.5 flex-shrink-0" />
                    <p className="text-[10px] text-blue-400/80 leading-relaxed">
                      Make sure your local model server is running before starting a build. AgentBrowser will route AI tasks through your local endpoint instead of cloud APIs.
                    </p>
                  </div>
                </div>
              )}

              {settings.modelProvider === 'cloud' && (
                <div className="p-4 rounded-xl border border-border/20 bg-background/20">
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    Cloud models are powered by the platform&apos;s built-in AI. For custom API keys (OpenAI, Anthropic, Groq), enable them in the <strong>Integrations</strong> tab.
                  </p>
                </div>
              )}
            </>
          )}

          {/* ══════ AGENTS TAB ══════ */}
          {tab === 'agents' && (
            <>
              <div>
                <SectionHeader icon={Bot} title="Custom Agents"
                  badge={
                    <span className="text-[10px] text-muted-foreground font-mono">
                      {settings.customAgents.filter(a => a.enabled).length}/{settings.customAgents.length} active
                    </span>
                  } />
                <p className="text-[11px] text-muted-foreground mb-4 leading-relaxed">
                  Upload agent configuration files (.json, .yaml, .md, .toml) to integrate custom agents into the build pipeline. Agents run during their designated phases automatically.
                </p>

                {/* Upload zone */}
                <button type="button" onClick={() => fileInputRef.current?.click()}
                  className="w-full p-6 rounded-xl border-2 border-dashed border-border/30 bg-background/10 hover:border-primary/30 hover:bg-primary/5 transition-all text-center group">
                  <FileUp className="w-6 h-6 mx-auto text-muted-foreground/40 group-hover:text-primary transition-colors mb-2" />
                  <p className="text-xs font-medium text-muted-foreground group-hover:text-foreground">
                    Click to upload agent config
                  </p>
                  <p className="text-[10px] text-muted-foreground/50 mt-1">
                    .json · .yaml · .yml · .md · .toml (max 512KB)
                  </p>
                </button>
                <input ref={fileInputRef} type="file" className="hidden"
                  accept=".json,.yaml,.yml,.md,.txt,.toml"
                  onChange={handleAgentUpload} />
              </div>

              {/* Agent list */}
              {settings.customAgents.length > 0 && (
                <div className="space-y-2">
                  {settings.customAgents.map(agent => (
                    <div key={agent.id}
                      className={`p-3 rounded-xl border transition-all ${
                        agent.enabled
                          ? 'border-primary/20 bg-primary/5'
                          : 'border-border/20 bg-background/20 opacity-60'
                      }`}>
                      <div className="flex items-start gap-3">
                        <button type="button" onClick={() => toggleAgent(agent.id)}
                          className="mt-0.5 flex-shrink-0">
                          {agent.enabled
                            ? <Power className="w-4 h-4 text-emerald-400" />
                            : <Power className="w-4 h-4 text-muted-foreground/40" />}
                        </button>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <input type="text" value={agent.name}
                              onChange={e => update('customAgents',
                                settings.customAgents.map(a => a.id === agent.id ? { ...a, name: e.target.value } : a)
                              )}
                              className="text-xs font-semibold text-foreground bg-transparent border-none outline-none p-0 flex-1 min-w-0" />
                            <span className="text-[9px] text-muted-foreground font-mono flex-shrink-0">
                              {agent.fileName}
                            </span>
                          </div>
                          <input type="text" value={agent.description} placeholder="Add description..."
                            onChange={e => update('customAgents',
                              settings.customAgents.map(a => a.id === agent.id ? { ...a, description: e.target.value } : a)
                            )}
                            className="text-[10px] text-muted-foreground bg-transparent border-none outline-none p-0 w-full mt-0.5" />
                        </div>
                        <button type="button" onClick={() => removeAgent(agent.id)}
                          className="p-1 rounded hover:bg-red-500/10 text-muted-foreground/40 hover:text-red-400 transition-colors flex-shrink-0">
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {settings.customAgents.length === 0 && (
                <div className="py-6 text-center text-xs text-muted-foreground/40">
                  <Bot className="w-6 h-6 mx-auto mb-2 opacity-30" />
                  No custom agents added yet
                </div>
              )}
            </>
          )}

          {/* ══════ INTEGRATIONS TAB ══════ */}
          {tab === 'integrations' && (
            <>
              <div className="flex items-center justify-between mb-1">
                <SectionHeader icon={Plug} title="3rd Party Integrations" />
                <span className="text-[10px] text-muted-foreground font-mono">
                  {settings.integrations.filter(i => i.enabled).length} enabled
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground mb-4 leading-relaxed">
                Enable integrations and add API keys. Each service is automatically wired into the correct build phase.
              </p>

              <div className="space-y-5">
                {INTEGRATION_GROUPS.map(group => {
                  const groupIntegrations = settings.integrations.filter(i => group.ids.includes(i.id));
                  if (groupIntegrations.length === 0) return null;
                  return (
                    <div key={group.label}>
                      <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">{group.label}</h4>
                      <div className="space-y-2">
                        {groupIntegrations.map(integration => (
                          <IntegrationRow key={integration.id} integration={integration}
                            onToggle={() => updateIntegration(integration.id, { enabled: !integration.enabled })}
                            onKeyChange={v => updateIntegration(integration.id, { apiKey: v })}
                            devMode={settings.mode === 'dev'} />
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>

              {settings.mode === 'dev' && (
                <button type="button"
                  onClick={() => {
                    const missing = DEFAULT_INTEGRATIONS.filter(
                      d => !settings.integrations.some(i => i.id === d.id)
                    );
                    if (missing.length) {
                      update('integrations', [...settings.integrations, ...missing]);
                    }
                  }}
                  className="w-full mt-4 py-2 rounded-lg text-[10px] font-medium text-muted-foreground border border-dashed border-border/30 hover:border-primary/30 hover:text-primary transition-all">
                  + Reset to default integrations
                </button>
              )}
            </>
          )}

          {/* ══════ CREDENTIALS TAB ══════ */}
          {tab === 'credentials' && (
            <>
              <div className="p-3 rounded-xl bg-muted/20 border border-border/20 mb-4">
                <p className="text-[11px] text-muted-foreground">
                  Tokens are stored in your browser only and sent via HTTPS as Bearer tokens to API proxy routes — never logged or persisted server-side.
                </p>
              </div>

              {/* GitHub */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
                  <span className="w-5 h-5 rounded flex items-center justify-center bg-foreground/10 text-[10px]">GH</span>
                  GitHub Personal Access Token
                </h3>
                <MaskedInput label="Token" value={creds.githubToken}
                  onChange={v => { setCreds(f => ({ ...f, githubToken: v })); setGhStatus('idle'); setDirty(true); }}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  helpText="Required scopes: repo · read:user · workflow"
                  hint={
                    <a href="https://github.com/settings/tokens/new?scopes=repo,read:user,workflow&description=AgentBrowser"
                      target="_blank" rel="noopener noreferrer"
                      className="inline-flex items-center gap-0.5 text-[10px] text-primary hover:underline">
                      Create token <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  } />
                <div className="flex items-center gap-2">
                  <button onClick={testGitHub}
                    disabled={!creds.githubToken.trim() || ghStatus === 'testing'}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium border border-border/30 bg-background/30 hover:bg-background/50 disabled:opacity-50 transition-colors">
                    {ghStatus === 'testing'
                      ? <><Loader2 className="w-3 h-3 animate-spin" />Testing...</>
                      : 'Test connection'}
                  </button>
                  {ghStatus === 'valid' && (
                    <span className="flex items-center gap-1 text-[11px] text-emerald-400">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Connected as @{ghUser}
                    </span>
                  )}
                  {ghStatus === 'invalid' && (
                    <span className="flex items-center gap-1 text-[11px] text-red-400">
                      <AlertCircle className="w-3.5 h-3.5" /> Invalid token
                    </span>
                  )}
                </div>
              </div>

              {/* Vercel */}
              <div className="space-y-3 mt-5">
                <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
                  <span className="w-5 h-5 rounded flex items-center justify-center bg-foreground/10 text-[10px]">▲</span>
                  Vercel Token
                </h3>
                <MaskedInput label="Token" value={creds.vercelToken}
                  onChange={v => { setCreds(f => ({ ...f, vercelToken: v })); setDirty(true); }}
                  placeholder="xxxxxxxxxxxxxxxxxxxxxxxx"
                  helpText="Used for creating projects and triggering deployments"
                  hint={
                    <a href="https://vercel.com/account/tokens" target="_blank" rel="noopener noreferrer"
                      className="inline-flex items-center gap-0.5 text-[10px] text-primary hover:underline">
                      Create token <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  } />
              </div>

              {/* Supabase */}
              <div className="space-y-3 mt-5">
                <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
                  <span className="w-5 h-5 rounded flex items-center justify-center bg-emerald-500/20 text-[10px] text-emerald-400">SB</span>
                  Supabase <span className="text-[9px] text-muted-foreground font-normal">(optional)</span>
                </h3>
                <MaskedInput label="Project URL" value={creds.supabaseUrl}
                  onChange={v => { setCreds(f => ({ ...f, supabaseUrl: v })); setDirty(true); }}
                  placeholder="https://xxxxxxxxxxxx.supabase.co" />
                <MaskedInput label="Service Role Key" value={creds.supabaseKey}
                  onChange={v => { setCreds(f => ({ ...f, supabaseKey: v })); setDirty(true); }}
                  placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI..."
                  helpText="Service role key — keeps RLS bypass for server operations only" />
              </div>

              {/* Clear all */}
              <div className="mt-5 pt-4 border-t border-border/20">
                <button onClick={() => {
                  clearCredentials();
                  setCreds({ githubToken: '', vercelToken: '', supabaseUrl: '', supabaseKey: '' });
                  setGhStatus('idle'); setGhUser('');
                }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] text-muted-foreground hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all">
                  <Trash2 className="w-3.5 h-3.5" />
                  Clear all credentials
                </button>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-border/20 flex items-center justify-between gap-2 flex-shrink-0">
          <span className="text-[10px] text-muted-foreground">
            {settings.mode === 'easy' ? 'Easy' : 'Developer'} mode · {settings.modelProvider === 'cloud' ? 'Cloud AI' : 'Local model'}
          </span>
          <div className="flex gap-2">
            <button onClick={onClose}
              className="px-4 py-1.5 rounded-lg text-[11px] font-medium border border-border/30 bg-background/30 hover:bg-background/50 text-muted-foreground transition-colors">
              Cancel
            </button>
            <button onClick={handleSave}
              disabled={!dirty}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-[11px] font-semibold text-white transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
              style={{ background: dirty ? 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.5 0.18 260))' : 'oklch(0.3 0 0)' }}>
              <CheckCircle2 className="w-3.5 h-3.5" />
              Save all
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Integration Row Sub-component ─── */

function IntegrationRow({ integration, onToggle, onKeyChange, devMode }: {
  integration: IntegrationConfig; onToggle: () => void; onKeyChange: (v: string) => void; devMode: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className={`rounded-xl border transition-all ${
      integration.enabled
        ? 'border-primary/20 bg-primary/5'
        : 'border-border/20 bg-background/20'
    }`}>
      <button type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-3 text-left">
        <button type="button" onClick={e => { e.stopPropagation(); onToggle(); }}
          className="flex-shrink-0">
          {integration.enabled
            ? <ToggleRight className="w-5 h-5 text-primary" />
            : <ToggleLeft className="w-5 h-5 text-muted-foreground/40" />}
        </button>
        <span className="text-xs font-medium text-foreground flex-1">{integration.name}</span>
        {devMode && (
          <span className="text-[9px] text-muted-foreground/50 font-mono">
            Phase {integration.phases.join(', ')}
          </span>
        )}
        {integration.enabled && integration.apiKey && (
          <CheckCircle2 className="w-3 h-3 text-emerald-400 flex-shrink-0" />
        )}
        {integration.enabled && !integration.apiKey && (
          <AlertCircle className="w-3 h-3 text-amber-400 flex-shrink-0" />
        )}
        <ChevronRight className={`w-3 h-3 text-muted-foreground/40 transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>
      {expanded && (
        <div className="px-3 pb-3 pt-0 space-y-2 animate-fade-in-up">
          <MaskedInput label="API Key" value={integration.apiKey} onChange={onKeyChange}
            placeholder={`${integration.name} API key`}
            helpText={`Wired into pipeline phase${integration.phases.length > 1 ? 's' : ''} ${integration.phases.join(', ')}`} />
        </div>
      )}
    </div>
  );
}
