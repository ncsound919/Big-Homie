'use client';

import { useState, useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import {
  KeyRound, X, Eye, EyeOff, CheckCircle2, AlertCircle, Loader2, Trash2, ExternalLink,
} from 'lucide-react';
import {
  getCredentials, saveCredentials, clearCredentials, type Credentials,
} from '@/lib/credentials';

interface CredentialsModalProps {
  open: boolean;
  onClose: () => void;
}

interface MaskedInputProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  helpText?: string;
  hint?: ReactNode;
}

function MaskedInput({ label, value, onChange, placeholder, helpText, hint }: MaskedInputProps) {
  const [show, setShow] = useState(false);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-2">
        <label className="text-xs font-medium text-foreground">{label}</label>
        {hint && <span className="text-[10px] text-muted-foreground">{hint}</span>}
      </div>
      <div className="relative">
        <input
          type={show ? 'text' : 'password'}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete="off"
          spellCheck={false}
          className="w-full pr-9 pl-3 py-2 text-xs rounded-lg border border-border/30 bg-background/40 text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-primary/40 font-mono"
        />
        <button
          type="button"
          onClick={() => setShow(v => !v)}
          tabIndex={-1}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-foreground transition-colors"
        >
          {show ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
        </button>
      </div>
      {helpText && <p className="text-[10px] text-muted-foreground/60">{helpText}</p>}
    </div>
  );
}

export default function CredentialsModal({ open, onClose }: CredentialsModalProps) {
  const [form, setForm] = useState<Credentials>({ githubToken: '', vercelToken: '', supabaseUrl: '', supabaseKey: '' });
  const [ghStatus, setGhStatus] = useState<'idle' | 'testing' | 'valid' | 'invalid'>('idle');
  const [ghUser, setGhUser] = useState('');
  const [saved, setSaved] = useState(false);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hydrateTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (open) {
      hydrateTimerRef.current = setTimeout(() => {
        setForm(getCredentials());
        setGhStatus('idle');
        setGhUser('');
        setSaved(false);
      }, 0);
    }

    return () => {
      if (hydrateTimerRef.current) clearTimeout(hydrateTimerRef.current);
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, [open]);

  const testGitHub = async () => {
    if (!form.githubToken.trim()) return;
    setGhStatus('testing');
    try {
      const res = await fetch('/api/github?action=user', {
        headers: { Authorization: `Bearer ${form.githubToken.trim()}` },
      });
      if (res.ok) {
        const data = await res.json() as { login?: string };
        setGhUser(data.login ?? '');
        setGhStatus('valid');
      } else {
        setGhStatus('invalid');
        setGhUser('');
      }
    } catch {
      setGhStatus('invalid');
      setGhUser('');
    }
  };

  const handleSave = () => {
    saveCredentials({
      githubToken: form.githubToken.trim(),
      vercelToken: form.vercelToken.trim(),
      supabaseUrl: form.supabaseUrl.trim(),
      supabaseKey: form.supabaseKey.trim(),
    });
    setSaved(true);
    saveTimerRef.current = setTimeout(() => { setSaved(false); onClose(); }, 800);
  };

  const handleClear = () => {
    clearCredentials();
    setForm({ githubToken: '', vercelToken: '', supabaseUrl: '', supabaseKey: '' });
    setGhStatus('idle');
    setGhUser('');
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-md rounded-2xl border border-border/30 bg-background shadow-2xl overflow-hidden animate-fade-in-up z-10">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border/20">
          <div className="flex items-center gap-2">
            <KeyRound className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-bold">Integration Credentials</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-background/60 text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-5 max-h-[70vh] overflow-y-auto">
          <p className="text-[11px] text-muted-foreground bg-muted/20 rounded-lg p-3 border border-border/20">
            Tokens are stored in your browser only and sent via HTTPS as Bearer tokens to the
            GitHub and Vercel APIs through this app&apos;s proxy routes — never logged or persisted server-side.
          </p>

          {/* GitHub */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
              <span className="w-5 h-5 rounded flex items-center justify-center bg-foreground/10">
                <span className="text-[10px]">GH</span>
              </span>
              GitHub Personal Access Token
            </h3>
            <MaskedInput
              label="Token"
              value={form.githubToken}
              onChange={v => { setForm(f => ({ ...f, githubToken: v })); setGhStatus('idle'); setGhUser(''); }}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
              helpText="Required scopes: repo · read:user · workflow"
              hint={
                <a
                  href="https://github.com/settings/tokens/new?scopes=repo,read:user,workflow&description=AgentBrowser"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-0.5 text-primary hover:underline"
                >
                  Create token <ExternalLink className="w-2.5 h-2.5" />
                </a>
              }
            />
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={testGitHub}
                disabled={!form.githubToken.trim() || ghStatus === 'testing'}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium border border-border/30 bg-background/30 hover:bg-background/50 disabled:opacity-50 transition-colors"
              >
                {ghStatus === 'testing'
                  ? <><Loader2 className="w-3 h-3 animate-spin" />Testing...</>
                  : 'Test connection'}
              </button>
              {ghStatus === 'valid' && (
                <span className="flex items-center gap-1 text-[11px] text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {ghUser ? `Connected as @${ghUser}` : 'Valid'}
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
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
              <span className="w-5 h-5 rounded flex items-center justify-center bg-foreground/10">
                <span className="text-[10px]">▲</span>
              </span>
              Vercel Token
            </h3>
            <MaskedInput
              label="Token"
              value={form.vercelToken}
              onChange={v => setForm(f => ({ ...f, vercelToken: v }))}
              placeholder="xxxxxxxxxxxxxxxxxxxxxxxx"
              helpText="Used for creating projects and triggering deployments via the Vercel API"
              hint={
                <a
                  href="https://vercel.com/account/tokens"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-0.5 text-primary hover:underline"
                >
                  Create token <ExternalLink className="w-2.5 h-2.5" />
                </a>
              }
            />
          </div>

          {/* Supabase */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
              <span className="w-5 h-5 rounded flex items-center justify-center bg-emerald-500/20">
                <span className="text-[10px] text-emerald-400">SB</span>
              </span>
              Supabase
              <span className="text-[9px] text-muted-foreground font-normal">(optional)</span>
            </h3>
            <MaskedInput
              label="Project URL"
              value={form.supabaseUrl}
              onChange={v => setForm(f => ({ ...f, supabaseUrl: v }))}
              placeholder="https://xxxxxxxxxxxx.supabase.co"
            />
            <MaskedInput
              label="Service Role Key"
              value={form.supabaseKey}
              onChange={v => setForm(f => ({ ...f, supabaseKey: v }))}
              placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI..."
              helpText="Service role key — keeps RLS bypass for server operations only"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-border/20 flex items-center justify-between gap-2">
          <button
            onClick={handleClear}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] text-muted-foreground hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear all
          </button>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg text-[11px] font-medium border border-border/30 bg-background/30 hover:bg-background/50 text-muted-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-[11px] font-semibold text-white transition-all hover:scale-105 active:scale-95"
              style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.5 0.18 260))' }}
            >
              {saved
                ? <><CheckCircle2 className="w-3.5 h-3.5 text-emerald-300" />Saved!</>
                : 'Save credentials'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
