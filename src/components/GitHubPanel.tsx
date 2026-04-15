'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import {
  Github, FolderOpen, File, ChevronRight, ChevronDown, ChevronUp,
  ArrowLeft, GitBranch, Loader2, CheckCheck, Search, RefreshCw,
  Code2, AlertCircle, GitCommit, ExternalLink, Copy, Check,
  Rocket, Database, Globe, Zap, Plus, Trash2, GitFork,
} from 'lucide-react';
import { getCredentials } from '@/lib/credentials';

/* ─── Types ─── */
interface GHRepo {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  private: boolean;
  updated_at: string;
  language: string | null;
  stargazers_count: number;
  default_branch: string;
}

interface GHTreeItem {
  name: string;
  path: string;
  type: 'file' | 'dir' | 'symlink';
  size?: number;
  sha: string;
}

interface GHFileData {
  content: string;
  sha: string;
  size: number;
  path: string;
  htmlUrl?: string;
}

interface EnvVar { key: string; value: string }

type PanelTab = 'repos' | 'editor' | 'deploy' | 'database';

/* ─── Helpers ─── */
const TEXT_EXTS = new Set([
  'ts', 'tsx', 'js', 'jsx', 'css', 'scss', 'html', 'json', 'md', 'mdx',
  'txt', 'env', 'yaml', 'yml', 'toml', 'sh', 'py', 'rs', 'go', 'java',
  'kt', 'swift', 'rb', 'php', 'sql', 'graphql', 'prisma', 'xml', 'svg',
  'lock', 'dockerfile', 'gitignore', 'prettierrc', 'eslintrc', 'nvmrc',
  'editorconfig', 'babelrc', 'npmrc', 'env.example', 'env.local',
]);

function isTextFile(name: string): boolean {
  const ext = name.toLowerCase().split('.').pop() ?? '';
  return TEXT_EXTS.has(ext) || ['dockerfile', 'makefile', 'readme', 'license'].includes(name.toLowerCase());
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

function timeSince(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const d = Math.floor(diff / 86400000);
  if (d === 0) return 'today';
  if (d === 1) return 'yesterday';
  if (d < 30) return `${d}d ago`;
  if (d < 365) return `${Math.floor(d / 30)}mo ago`;
  return `${Math.floor(d / 365)}y ago`;
}

/* ═══ Deploy Tab ═══════════════════════════════════════════════════════════ */
function DeployTab({
  selectedRepo,
  vercelToken,
}: {
  selectedRepo: GHRepo | null;
  vercelToken: string;
}) {
  const [projectName, setProjectName] = useState(selectedRepo?.name ?? '');
  const [framework, setFramework] = useState('nextjs');
  const [rootDir, setRootDir] = useState('');
  const [envVars, setEnvVars] = useState<EnvVar[]>([{ key: '', value: '' }]);
  const [deploying, setDeploying] = useState(false);
  const [result, setResult] = useState<{ projectUrl: string; dashboardUrl: string } | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (selectedRepo) setProjectName(selectedRepo.name);
  }, [selectedRepo?.name]);

  const addEnvVar = () => setEnvVars(v => [...v, { key: '', value: '' }]);
  const removeEnvVar = (i: number) => setEnvVars(v => v.filter((_, idx) => idx !== i));
  const updateEnvVar = (i: number, field: 'key' | 'value', val: string) =>
    setEnvVars(v => v.map((e, idx) => idx === i ? { ...e, [field]: val } : e));

  const deploy = async () => {
    if (!vercelToken) {
      setError('Configure your Vercel token in Settings (key icon)');
      return;
    }
    if (!projectName.trim()) { setError('Project name required'); return; }
    setDeploying(true);
    setError('');
    setResult(null);
    try {
      const res = await fetch('/api/deploy', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${vercelToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          projectName: projectName.trim(),
          gitRepo: selectedRepo?.full_name,
          framework,
          rootDirectory: rootDir || undefined,
          envVars: envVars.filter(e => e.key.trim()),
        }),
      });
      const data = await res.json() as { projectUrl?: string; dashboardUrl?: string; error?: string };
      if (!res.ok || data.error) throw new Error(data.error ?? 'Deploy failed');
      if (!data.projectUrl || !data.dashboardUrl) throw new Error('Incomplete response from Vercel');
      setResult({ projectUrl: data.projectUrl, dashboardUrl: data.dashboardUrl });
      toast.success('Vercel project created!', { description: data.projectUrl });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Deploy failed');
    } finally {
      setDeploying(false);
    }
  };

  const FRAMEWORKS = [
    { value: 'nextjs', label: 'Next.js' },
    { value: 'react', label: 'Create React App' },
    { value: 'vite', label: 'Vite' },
    { value: 'nuxtjs', label: 'Nuxt.js' },
    { value: 'sveltekit', label: 'SvelteKit' },
    { value: 'astro', label: 'Astro' },
    { value: 'remix', label: 'Remix' },
    { value: 'gatsby', label: 'Gatsby' },
    { value: null, label: 'Other / Static' },
  ];

  return (
    <div className="space-y-4 max-w-lg">
      {!vercelToken && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          Configure your Vercel token in Settings to enable deployments.
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-[11px] font-medium text-foreground/80">Project name</label>
          <input
            value={projectName}
            onChange={e => setProjectName(e.target.value)}
            placeholder="my-project"
            className="w-full px-3 py-2 text-xs rounded-lg border border-border/30 bg-background/30 text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-primary/40"
          />
        </div>
        <div className="space-y-1">
          <label className="text-[11px] font-medium text-foreground/80">Framework</label>
          <select
            value={framework}
            onChange={e => setFramework(e.target.value)}
            className="w-full px-3 py-2 text-xs rounded-lg border border-border/30 bg-background/30 text-foreground focus:outline-none focus:border-primary/40"
          >
            {FRAMEWORKS.map(f => (
              <option key={f.value ?? 'null'} value={f.value ?? ''}>{f.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Connected repo */}
      {selectedRepo && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-background/20 border border-border/20 text-xs">
          <GitFork className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-foreground/80 font-mono">{selectedRepo.full_name}</span>
          <span className="ml-auto text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/10 px-1.5 py-0.5 rounded-full">connected</span>
        </div>
      )}

      <div className="space-y-1">
        <label className="text-[11px] font-medium text-foreground/80">Root directory <span className="text-muted-foreground font-normal">(optional)</span></label>
        <input
          value={rootDir}
          onChange={e => setRootDir(e.target.value)}
          placeholder="e.g. apps/web"
          className="w-full px-3 py-2 text-xs rounded-lg border border-border/30 bg-background/30 text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-primary/40"
        />
      </div>

      {/* Env vars */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[11px] font-medium text-foreground/80">Environment variables</label>
          <button onClick={addEnvVar} className="flex items-center gap-1 text-[10px] text-primary hover:underline">
            <Plus className="w-3 h-3" /> Add
          </button>
        </div>
        {envVars.map((ev, i) => (
          <div key={i} className="flex gap-1.5">
            <input
              value={ev.key}
              onChange={e => updateEnvVar(i, 'key', e.target.value)}
              placeholder="KEY"
              className="flex-1 px-2 py-1.5 text-[11px] font-mono rounded-lg border border-border/20 bg-background/20 text-foreground placeholder:text-muted-foreground/30 focus:outline-none focus:border-primary/30"
            />
            <input
              value={ev.value}
              onChange={e => updateEnvVar(i, 'value', e.target.value)}
              placeholder="value"
              className="flex-[2] px-2 py-1.5 text-[11px] font-mono rounded-lg border border-border/20 bg-background/20 text-foreground placeholder:text-muted-foreground/30 focus:outline-none focus:border-primary/30"
            />
            <button
              onClick={() => removeEnvVar(i)}
              className="p-1.5 rounded hover:text-red-400 text-muted-foreground/40 transition-colors"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          {error}
        </div>
      )}

      {result && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-2">
          <p className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
            <CheckCheck className="w-3.5 h-3.5" /> Project created on Vercel
          </p>
          <a href={result.projectUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-[11px] text-foreground hover:text-primary transition-colors font-mono">
            <Globe className="w-3 h-3" /> {result.projectUrl}
          </a>
          <a href={result.dashboardUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-primary transition-colors">
            <ExternalLink className="w-3 h-3" /> Open Vercel dashboard
          </a>
        </div>
      )}

      <button
        onClick={deploy}
        disabled={deploying || !projectName.trim()}
        className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:scale-105 active:scale-95"
        style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.5 0.18 260))' }}
      >
        {deploying
          ? <><Loader2 className="w-4 h-4 animate-spin" />Creating project...</>
          : <><Rocket className="w-4 h-4" />Deploy to Vercel</>}
      </button>
    </div>
  );
}

/* ═══ Database Tab ══════════════════════════════════════════════════════════ */
function DatabaseTab({ supabaseUrl, supabaseKey }: { supabaseUrl: string; supabaseKey: string }) {
  const [copied, setCopied] = useState('');

  const copy = (text: string, key: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(key);
      setTimeout(() => setCopied(''), 1800);
    });
  };

  const isConfigured = supabaseUrl.trim().length > 10;
  const dbUrl = isConfigured
    ? supabaseUrl.replace('https://', 'postgresql://postgres:[YOUR-PASSWORD]@').replace('.supabase.co', '.supabase.co:5432/postgres')
    : '';

  const prismaSnippet = `// prisma/schema.prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  directUrl = env("DIRECT_URL")
}`;

  const envSnippet = isConfigured
    ? `DATABASE_URL="${dbUrl}"\nDIRECT_URL="${dbUrl}"\nNEXT_PUBLIC_SUPABASE_URL="${supabaseUrl}"\nNEXT_PUBLIC_SUPABASE_ANON_KEY="[YOUR-ANON-KEY]"`
    : '';

  const PROVIDERS = [
    { name: 'Supabase', desc: 'Postgres + Auth + Storage — free tier', url: 'https://supabase.com/dashboard/new/project', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
    { name: 'Neon', desc: 'Serverless Postgres — branching per PR', url: 'https://console.neon.tech/signup', color: 'text-teal-400', bg: 'bg-teal-500/10', border: 'border-teal-500/20' },
    { name: 'PlanetScale', desc: 'MySQL-compatible with schema branching', url: 'https://app.planetscale.com/sign-up', color: 'text-violet-400', bg: 'bg-violet-500/10', border: 'border-violet-500/20' },
    { name: 'Turso', desc: 'Edge SQLite — ultra-low latency', url: 'https://turso.tech/', color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20' },
  ];

  return (
    <div className="space-y-5">
      {/* Supabase status */}
      {isConfigured ? (
        <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 space-y-3">
          <p className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
            <CheckCheck className="w-3.5 h-3.5" /> Supabase connected
          </p>
          <p className="text-[10px] text-muted-foreground font-mono break-all">{supabaseUrl}</p>

          <div className="space-y-2">
            <label className="text-[10px] text-muted-foreground">DATABASE_URL (Prisma)</label>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-[10px] font-mono text-foreground/70 bg-background/30 px-2 py-1.5 rounded-lg border border-border/20 truncate">{dbUrl}</code>
              <button onClick={() => copy(dbUrl, 'dburl')} className="p-1.5 rounded hover:text-primary text-muted-foreground/50 transition-colors flex-shrink-0">
                {copied === 'dburl' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] text-muted-foreground">.env.local snippet</label>
            <div className="relative">
              <pre className="text-[10px] font-mono text-foreground/70 bg-background/30 p-3 rounded-lg border border-border/20 overflow-x-auto whitespace-pre-wrap">{envSnippet}</pre>
              <button onClick={() => copy(envSnippet, 'env')} className="absolute top-2 right-2 p-1.5 rounded bg-background/60 hover:text-primary text-muted-foreground/50 transition-colors">
                {copied === 'env' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          Configure Supabase URL in Settings for connection strings and env snippets.
        </div>
      )}

      {/* Prisma schema snippet */}
      <div className="space-y-2">
        <label className="text-[11px] font-medium text-foreground/80 flex items-center gap-1.5">
          <Database className="w-3.5 h-3.5 text-cyan-400" /> Prisma datasource snippet
        </label>
        <div className="relative">
          <pre className="text-[10px] font-mono text-cyan-300/80 bg-background/30 p-3 rounded-lg border border-border/20 overflow-x-auto">{prismaSnippet}</pre>
          <button onClick={() => copy(prismaSnippet, 'prisma')} className="absolute top-2 right-2 p-1.5 rounded bg-background/60 hover:text-primary text-muted-foreground/50 transition-colors">
            {copied === 'prisma' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          </button>
        </div>
      </div>

      {/* Provider links */}
      <div className="space-y-2">
        <p className="text-[11px] font-medium text-foreground/80">Recommended providers</p>
        <div className="grid grid-cols-2 gap-2">
          {PROVIDERS.map(p => (
            <a
              key={p.name}
              href={p.url}
              target="_blank"
              rel="noopener noreferrer"
              className={`group p-3 rounded-xl border ${p.border} ${p.bg} hover:scale-[1.02] transition-all flex items-start gap-2`}
            >
              <Zap className={`w-3.5 h-3.5 ${p.color} mt-0.5 flex-shrink-0`} />
              <div className="min-w-0">
                <p className={`text-xs font-semibold ${p.color}`}>{p.name}</p>
                <p className="text-[10px] text-muted-foreground leading-tight">{p.desc}</p>
              </div>
              <ExternalLink className="w-3 h-3 text-muted-foreground/30 ml-auto group-hover:text-muted-foreground/60 flex-shrink-0 mt-0.5" />
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ═══ Main Component ════════════════════════════════════════════════════════ */
export default function GitHubPanel() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [tab, setTab] = useState<PanelTab>('repos');

  /* Credentials */
  const [token, setToken] = useState('');
  const [vercelToken, setVercelToken] = useState('');
  const [supabaseUrl, setSupabaseUrl] = useState('');
  const [supabaseKey, setSupabaseKey] = useState('');
  const tokenRef = useRef('');

  /* Repos */
  const [repos, setRepos] = useState<GHRepo[]>([]);
  const [repoSearch, setRepoSearch] = useState('');
  const [reposLoading, setReposLoading] = useState(false);
  const [repoError, setRepoError] = useState('');

  /* Selected repo + file tree */
  const [selectedRepo, setSelectedRepo] = useState<GHRepo | null>(null);
  const [branch, setBranch] = useState('');
  const branchRef = useRef('');
  const [branches, setBranches] = useState<string[]>([]);
  const [treePath, setTreePath] = useState('');
  const [treeItems, setTreeItems] = useState<GHTreeItem[]>([]);
  const [treeLoading, setTreeLoading] = useState(false);

  /* File editor */
  const [selectedFile, setSelectedFile] = useState('');
  const [fileData, setFileData] = useState<GHFileData | null>(null);
  const [editedContent, setEditedContent] = useState('');
  const [fileLoading, setFileLoading] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  /* Commit */
  const [commitMsg, setCommitMsg] = useState('');
  const [committing, setCommitting] = useState(false);
  const [commitSuccess, setCommitSuccess] = useState(false);
  const [commitError, setCommitError] = useState('');

  /* New branch */
  const [showNewBranch, setShowNewBranch] = useState(false);
  const [newBranchName, setNewBranchName] = useState('');
  const [creatingBranch, setCreatingBranch] = useState(false);

  /* Guards against concurrent fetches */
  const fetchingReposRef = useRef(false);
  const selectingRepoRef = useRef(0); // incremented on each selectRepo call

  /* Load credentials from localStorage + listen for updates */
  const loadCreds = useCallback(() => {
    const creds = getCredentials();
    const newToken = creds.githubToken;
    if (newToken !== tokenRef.current) {
      tokenRef.current = newToken;
      setToken(newToken);
      setRepos([]);
      setSelectedRepo(null);
      setTreeItems([]);
      setSelectedFile('');
      setFileData(null);
      setEditedContent('');
    }
    setVercelToken(creds.vercelToken);
    setSupabaseUrl(creds.supabaseUrl);
    setSupabaseKey(creds.supabaseKey);
  }, []);

  useEffect(() => {
    loadCreds();
    window.addEventListener('ab:credentials-changed', loadCreds);
    return () => window.removeEventListener('ab:credentials-changed', loadCreds);
  }, [loadCreds]);

  /* Keep branchRef in sync */
  useEffect(() => { branchRef.current = branch; }, [branch]);

  /* ─── API helpers ─── */
  const makeHeaders = useCallback(() => ({
    Authorization: `Bearer ${tokenRef.current}`,
    'Content-Type': 'application/json',
  }), []);

  /* ─── Fetch repos ─── */
  const fetchRepos = useCallback(async () => {
    if (!tokenRef.current) {
      setRepoError('Configure your GitHub token in Settings (key icon in the header)');
      return;
    }
    if (fetchingReposRef.current) return; // prevent concurrent fetches
    fetchingReposRef.current = true;
    setReposLoading(true);
    setRepoError('');
    try {
      const res = await fetch('/api/github?action=repos', { headers: makeHeaders() });
      if (!res.ok) {
        const data = await res.json() as { error?: string };
        throw new Error(res.status === 401 ? 'Invalid GitHub token' : (data.error ?? 'Failed to fetch repos'));
      }
      const data = await res.json() as GHRepo[];
      setRepos(Array.isArray(data) ? data : []);
    } catch (e) {
      setRepoError(e instanceof Error ? e.message : 'Failed to load repos');
    } finally {
      setReposLoading(false);
      fetchingReposRef.current = false;
    }
  }, [makeHeaders]);

  /* Auto-fetch on expand */
  useEffect(() => {
    if (isExpanded && tokenRef.current && repos.length === 0) {
      fetchRepos();
    }
  }, [isExpanded, repos.length, fetchRepos]);

  /* ─── Fetch branches ─── */
  const fetchBranches = useCallback(async (repo: GHRepo) => {
    const [owner, repoName] = repo.full_name.split('/');
    const params = new URLSearchParams({ action: 'branches', owner, repo: repoName });
    const res = await fetch(`/api/github?${params}`, { headers: makeHeaders() });
    if (res.ok) {
      const data = await res.json() as Array<{ name: string }>;
      setBranches(data.map(b => b.name));
    }
  }, [makeHeaders]);

  /* ─── Fetch file tree ─── */
  const fetchTree = useCallback(async (repo: GHRepo, path: string, overrideBranch?: string) => {
    setTreeLoading(true);
    try {
      const [owner, repoName] = repo.full_name.split('/');
      const b = overrideBranch ?? branchRef.current;
      const params = new URLSearchParams({ action: 'tree', owner, repo: repoName, path, ref: b });
      const res = await fetch(`/api/github?${params}`, { headers: makeHeaders() });
      if (!res.ok) throw new Error('Failed to fetch directory');
      const data = await res.json() as GHTreeItem[];
      const sorted = [...data].sort((a, b) => {
        if (a.type !== b.type) return a.type === 'dir' ? -1 : 1;
        return a.name.localeCompare(b.name);
      });
      setTreeItems(sorted);
      setTreePath(path);
    } catch (e) {
      toast.error('Failed to load directory', { description: e instanceof Error ? e.message : undefined });
    } finally {
      setTreeLoading(false);
    }
  }, [makeHeaders]);

  /* ─── Select repo ─── */
  const selectRepo = useCallback(async (repo: GHRepo) => {
    const callId = ++selectingRepoRef.current;
    setSelectedRepo(repo);
    setBranch(repo.default_branch);
    branchRef.current = repo.default_branch;
    setTreePath('');
    setSelectedFile('');
    setFileData(null);
    setEditedContent('');
    setIsDirty(false);
    setTab('editor');
    await fetchBranches(repo);
    if (selectingRepoRef.current !== callId) return; // stale — user picked a different repo
    await fetchTree(repo, '', repo.default_branch);
  }, [fetchTree, fetchBranches]);

  /* ─── Navigate up ─── */
  const navigateUp = useCallback(() => {
    if (!selectedRepo || !treePath) return;
    const parts = treePath.split('/');
    parts.pop();
    fetchTree(selectedRepo, parts.join('/'));
  }, [selectedRepo, treePath, fetchTree]);

  /* ─── Select file or dir ─── */
  const selectItem = useCallback(async (item: GHTreeItem) => {
    if (!selectedRepo) return;
    if (item.type === 'dir') {
      await fetchTree(selectedRepo, item.path);
      return;
    }
    if (!isTextFile(item.name)) {
      toast.warning(`Binary or unsupported file: ${item.name}`);
      return;
    }
    setFileLoading(true);
    setSelectedFile(item.path);
    try {
      const [owner, repoName] = selectedRepo.full_name.split('/');
      const params = new URLSearchParams({ action: 'file', owner, repo: repoName, path: item.path, ref: branchRef.current });
      const res = await fetch(`/api/github?${params}`, { headers: makeHeaders() });
      if (!res.ok) throw new Error('Failed to read file');
      const data = await res.json() as GHFileData;
      setFileData(data);
      setEditedContent(data.content);
      setIsDirty(false);
      setCommitError('');
    } catch (e) {
      toast.error('Failed to load file', { description: e instanceof Error ? e.message : undefined });
      setSelectedFile('');
    } finally {
      setFileLoading(false);
    }
  }, [selectedRepo, makeHeaders, fetchTree]);

  /* ─── Editor change ─── */
  const handleEditorChange = useCallback((value: string) => {
    setEditedContent(value);
    setIsDirty(fileData ? value !== fileData.content : false);
  }, [fileData]);

  /* Tab key in editor */
  const handleEditorKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const ta = e.currentTarget;
      const start = ta.selectionStart;
      const end = ta.selectionEnd;
      const newVal = editedContent.substring(0, start) + '  ' + editedContent.substring(end);
      handleEditorChange(newVal);
      requestAnimationFrame(() => { ta.selectionStart = ta.selectionEnd = start + 2; });
    }
  }, [editedContent, handleEditorChange]);

  /* ─── Commit file ─── */
  const commitFile = useCallback(async () => {
    if (!selectedRepo || !selectedFile || !fileData?.sha || !commitMsg.trim()) return;
    setCommitting(true);
    setCommitError('');
    try {
      const [owner, repoName] = selectedRepo.full_name.split('/');
      const res = await fetch('/api/github', {
        method: 'PUT',
        headers: makeHeaders(),
        body: JSON.stringify({
          owner, repo: repoName,
          path: selectedFile,
          content: editedContent,
          sha: fileData.sha,
          message: commitMsg,
          branch: branchRef.current,
        }),
      });
      const data = await res.json() as { success?: boolean; error?: string; newFileSha?: string; commitUrl?: string };
      if (!res.ok || data.error) throw new Error(data.error ?? 'Commit failed');
      // Update sha so next commit works
      setFileData(prev => prev ? { ...prev, sha: data.newFileSha ?? prev.sha, content: editedContent } : null);
      setIsDirty(false);
      setCommitMsg('');
      setCommitSuccess(true);
      toast.success('Committed successfully!', { description: `${selectedFile} on ${branchRef.current}` });
      setTimeout(() => setCommitSuccess(false), 3000);
    } catch (e) {
      setCommitError(e instanceof Error ? e.message : 'Commit failed');
    } finally {
      setCommitting(false);
    }
  }, [selectedRepo, selectedFile, fileData, commitMsg, editedContent, makeHeaders]);

  /* ─── Create branch ─── */
  const createBranch = useCallback(async () => {
    if (!selectedRepo || !newBranchName.trim()) return;
    setCreatingBranch(true);
    try {
      const [owner, repoName] = selectedRepo.full_name.split('/');
      const res = await fetch('/api/github', {
        method: 'POST',
        headers: makeHeaders(),
        body: JSON.stringify({ owner, repo: repoName, newBranch: newBranchName.trim(), fromBranch: branchRef.current }),
      });
      const data = await res.json() as { success?: boolean; error?: string };
      if (!res.ok || data.error) throw new Error(data.error ?? 'Branch creation failed');
      await fetchBranches(selectedRepo);
      setBranch(newBranchName.trim());
      branchRef.current = newBranchName.trim();
      setNewBranchName('');
      setShowNewBranch(false);
      toast.success(`Branch created: ${newBranchName.trim()}`);
    } catch (e) {
      toast.error('Branch creation failed', { description: e instanceof Error ? e.message : undefined });
    } finally {
      setCreatingBranch(false);
    }
  }, [selectedRepo, newBranchName, makeHeaders, fetchBranches]);

  /* ─── Render ─── */
  const filteredRepos = repos.filter(r =>
    r.name.toLowerCase().includes(repoSearch.toLowerCase()) ||
    (r.description ?? '').toLowerCase().includes(repoSearch.toLowerCase())
  );

  const breadcrumbs = treePath ? ['root', ...treePath.split('/')] : ['root'];

  const TABS: { id: PanelTab; label: string; icon: React.ReactNode }[] = [
    { id: 'repos',    label: 'Repos',    icon: <Github className="w-3 h-3" /> },
    { id: 'editor',   label: 'Editor',   icon: <Code2 className="w-3 h-3" /> },
    { id: 'deploy',   label: 'Deploy',   icon: <Rocket className="w-3 h-3" /> },
    { id: 'database', label: 'Database', icon: <Database className="w-3 h-3" /> },
  ];

  return (
    <div className="w-full rounded-2xl border border-border/30 bg-background/20 overflow-hidden">
      {/* ─── Collapsible header ─── */}
      <button
        onClick={() => setIsExpanded(v => !v)}
        className="w-full px-4 sm:px-6 py-3.5 flex items-center justify-between hover:bg-background/30 transition-colors group"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <Github className="w-4 h-4 text-foreground/70 flex-shrink-0" />
          <span className="text-sm font-semibold">GitHub Workspace</span>
          {selectedRepo && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20 truncate max-w-[180px]">
              {selectedRepo.full_name}
            </span>
          )}
          {!token && (
            <span className="text-[9px] font-medium text-amber-400 border border-amber-500/20 bg-amber-500/10 px-1.5 py-0.5 rounded-full flex-shrink-0">
              token needed
            </span>
          )}
          {token && repos.length > 0 && (
            <span className="text-[9px] font-medium text-emerald-400 border border-emerald-500/20 bg-emerald-500/10 px-1.5 py-0.5 rounded-full flex-shrink-0">
              {repos.length} repos
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-[10px] text-muted-foreground/50 group-hover:text-muted-foreground transition-colors hidden sm:block">
            {isExpanded ? 'collapse' : 'browse & edit GitHub repos'}
          </span>
          {isExpanded
            ? <ChevronUp className="w-4 h-4 text-muted-foreground" />
            : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-border/20">
          {/* Tab bar */}
          <div className="flex items-center gap-1 px-4 sm:px-6 pt-3 border-b border-border/20">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-t-lg text-[11px] font-medium transition-colors ${
                  tab === t.id
                    ? 'bg-background/50 border border-border/30 border-b-background -mb-px text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {t.icon}
                {t.label}
              </button>
            ))}
          </div>

          <div className="p-4 sm:p-5">
            {/* ══ REPOS TAB ══ */}
            {tab === 'repos' && (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground/50" />
                    <input
                      value={repoSearch}
                      onChange={e => setRepoSearch(e.target.value)}
                      placeholder="Search repos..."
                      className="w-full pl-8 pr-3 py-2 text-xs rounded-lg border border-border/30 bg-background/30 text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-primary/40"
                    />
                  </div>
                  <button
                    onClick={fetchRepos}
                    disabled={reposLoading}
                    className="px-3 py-2 rounded-lg border border-border/30 bg-background/30 text-muted-foreground hover:text-foreground disabled:opacity-50 transition-colors"
                    title="Refresh"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${reposLoading ? 'animate-spin' : ''}`} />
                  </button>
                </div>

                {repoError && (
                  <div className="flex items-start gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                    <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                    {repoError}
                  </div>
                )}

                {reposLoading ? (
                  <div className="flex items-center justify-center py-10 gap-2 text-xs text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" /> Loading repos...
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[400px] overflow-y-auto pr-1">
                    {filteredRepos.map(repo => (
                      <button
                        key={repo.id}
                        onClick={() => selectRepo(repo)}
                        className={`group p-3 rounded-xl text-left border transition-all duration-200 hover:scale-[1.01] ${
                          selectedRepo?.id === repo.id
                            ? 'border-primary/40 bg-primary/10'
                            : 'border-border/20 bg-background/20 hover:border-border/40 hover:bg-background/40'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="text-xs font-semibold text-foreground truncate">{repo.name}</span>
                              {repo.private && (
                                <span className="text-[8px] px-1 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">private</span>
                              )}
                              {repo.language && (
                                <span className="text-[8px] px-1 py-0.5 rounded bg-muted/40 text-muted-foreground">{repo.language}</span>
                              )}
                            </div>
                            {repo.description && (
                              <p className="text-[10px] text-muted-foreground mt-0.5 line-clamp-1">{repo.description}</p>
                            )}
                          </div>
                          <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/40 flex-shrink-0 group-hover:text-primary transition-colors" />
                        </div>
                        <div className="flex items-center gap-3 mt-1.5 text-[9px] text-muted-foreground/50">
                          <span className="flex items-center gap-0.5"><GitBranch className="w-2.5 h-2.5" />{repo.default_branch}</span>
                          <span>{timeSince(repo.updated_at)}</span>
                        </div>
                      </button>
                    ))}
                    {filteredRepos.length === 0 && !reposLoading && (
                      <div className="col-span-2 text-center py-10 text-xs text-muted-foreground">
                        {repos.length === 0
                          ? 'No repos loaded. Configure your GitHub token in Settings and refresh.'
                          : 'No repos match your search.'}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ══ EDITOR TAB ══ */}
            {tab === 'editor' && (
              <div>
                {!selectedRepo ? (
                  <div className="text-center py-12 text-xs text-muted-foreground">
                    <Github className="w-10 h-10 mx-auto mb-3 opacity-20" />
                    <p>Select a repo from the <button onClick={() => setTab('repos')} className="text-primary underline">Repos tab</button> to browse and edit files</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {/* Branch bar */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <GitBranch className="w-3.5 h-3.5 text-muted-foreground" />
                      <select
                        value={branch}
                        onChange={e => {
                          setBranch(e.target.value);
                          branchRef.current = e.target.value;
                          if (selectedRepo) fetchTree(selectedRepo, treePath, e.target.value);
                        }}
                        className="text-[11px] bg-background/40 border border-border/20 rounded-lg px-2 py-1 text-foreground focus:outline-none focus:border-primary/40"
                      >
                        {branches.map(b => <option key={b} value={b}>{b}</option>)}
                      </select>
                      <button
                        onClick={() => setShowNewBranch(v => !v)}
                        className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-primary transition-colors"
                      >
                        <Plus className="w-3 h-3" /> New branch
                      </button>
                      {fileData?.htmlUrl && (
                        <a
                          href={fileData.htmlUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-auto flex items-center gap-1 text-[10px] text-muted-foreground hover:text-primary transition-colors"
                        >
                          <ExternalLink className="w-3 h-3" /> View on GitHub
                        </a>
                      )}
                    </div>

                    {/* New branch input */}
                    {showNewBranch && (
                      <div className="flex items-center gap-2 p-2 rounded-lg bg-background/30 border border-border/20">
                        <GitFork className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                        <input
                          value={newBranchName}
                          onChange={e => setNewBranchName(e.target.value)}
                          placeholder={`feature/my-branch (from ${branch})`}
                          className="flex-1 text-[11px] bg-transparent text-foreground placeholder:text-muted-foreground/40 focus:outline-none"
                          onKeyDown={e => e.key === 'Enter' && createBranch()}
                        />
                        <button
                          onClick={createBranch}
                          disabled={!newBranchName.trim() || creatingBranch}
                          className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-medium bg-primary/20 text-primary border border-primary/30 hover:bg-primary/30 disabled:opacity-50 transition-colors"
                        >
                          {creatingBranch ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Create'}
                        </button>
                        <button onClick={() => setShowNewBranch(false)} className="p-1 rounded text-muted-foreground/50 hover:text-foreground">
                          <ChevronUp className="w-3 h-3" />
                        </button>
                      </div>
                    )}

                    {/* 3-panel file browser */}
                    <div className="grid grid-cols-1 lg:grid-cols-5 gap-3" style={{ height: '500px' }}>
                      {/* File tree */}
                      <div className="lg:col-span-2 flex flex-col border border-border/20 rounded-xl overflow-hidden bg-background/20">
                        {/* Tree path header */}
                        <div className="px-3 py-2 border-b border-border/20 flex items-center gap-2 flex-shrink-0">
                          {treePath && (
                            <button
                              onClick={navigateUp}
                              className="p-1 rounded hover:bg-background/40 text-muted-foreground hover:text-foreground transition-colors"
                              title="Go up"
                            >
                              <ArrowLeft className="w-3 h-3" />
                            </button>
                          )}
                          <div className="flex items-center gap-0.5 text-[10px] text-muted-foreground min-w-0 flex-1 overflow-hidden">
                            {breadcrumbs.map((crumb, i) => (
                              <span key={i} className="flex items-center gap-0.5 min-w-0">
                                {i > 0 && <ChevronRight className="w-2.5 h-2.5 opacity-40 flex-shrink-0" />}
                                <span className={`truncate ${i === breadcrumbs.length - 1 ? 'text-foreground/70' : 'opacity-60'}`}>{crumb}</span>
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* Items list */}
                        <div className="flex-1 overflow-y-auto">
                          {treeLoading
                            ? (
                              <div className="flex items-center justify-center h-full text-muted-foreground gap-2 text-xs">
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              </div>
                            )
                            : treeItems.length === 0
                              ? <div className="flex items-center justify-center h-full text-[11px] text-muted-foreground/50">Empty directory</div>
                              : (
                                <div>
                                  {treeItems.map(item => (
                                    <button
                                      key={item.path}
                                      onClick={() => selectItem(item)}
                                      className={`w-full flex items-center gap-2 px-3 py-1.5 text-left text-[11px] hover:bg-background/40 transition-colors ${
                                        selectedFile === item.path ? 'bg-primary/10 text-primary' : 'text-foreground/80'
                                      }`}
                                    >
                                      {item.type === 'dir'
                                        ? <FolderOpen className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                                        : <File className="w-3.5 h-3.5 text-cyan-400/70 flex-shrink-0" />}
                                      <span className="truncate font-mono">{item.name}</span>
                                      {item.type === 'file' && item.size != null && (
                                        <span className="ml-auto text-[8px] text-muted-foreground/40 flex-shrink-0">{formatBytes(item.size)}</span>
                                      )}
                                      {item.type === 'dir' && <ChevronRight className="ml-auto w-3 h-3 text-muted-foreground/30 flex-shrink-0" />}
                                    </button>
                                  ))}
                                </div>
                              )
                          }
                        </div>
                      </div>

                      {/* Code editor */}
                      <div className="lg:col-span-3 flex flex-col border border-border/20 rounded-xl overflow-hidden bg-background/20">
                        {/* Editor header */}
                        <div className="px-3 py-2 border-b border-border/20 flex items-center gap-2 flex-shrink-0">
                          <Code2 className="w-3.5 h-3.5 text-cyan-400/70 flex-shrink-0" />
                          <span className="text-[10px] font-mono text-muted-foreground truncate flex-1">
                            {selectedFile || 'No file selected'}
                          </span>
                          {isDirty && (
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0 animate-pulse" title="Unsaved changes" />
                          )}
                        </div>

                        {/* Textarea */}
                        {fileLoading
                          ? (
                            <div className="flex-1 flex items-center justify-center gap-2 text-xs text-muted-foreground">
                              <Loader2 className="w-4 h-4 animate-spin" /> Loading...
                            </div>
                          )
                          : !selectedFile
                            ? (
                              <div className="flex-1 flex items-center justify-center text-xs text-muted-foreground text-center px-4">
                                Select a file from the tree to edit it
                              </div>
                            )
                            : (
                              <textarea
                                value={editedContent}
                                onChange={e => handleEditorChange(e.target.value)}
                                onKeyDown={handleEditorKeyDown}
                                className="flex-1 resize-none bg-transparent text-[11px] font-mono text-foreground/90 p-3 focus:outline-none leading-[1.6] overflow-auto"
                                spellCheck={false}
                                autoCorrect="off"
                                autoCapitalize="off"
                              />
                            )
                        }

                        {/* Commit bar */}
                        {selectedFile && !fileLoading && (
                          <div className="border-t border-border/20 p-2.5 flex items-center gap-2 flex-shrink-0">
                            <input
                              value={commitMsg}
                              onChange={e => setCommitMsg(e.target.value)}
                              placeholder="Commit message..."
                              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && commitFile()}
                              className="flex-1 text-[11px] px-3 py-1.5 rounded-lg border border-border/20 bg-background/30 text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-primary/40"
                            />
                            <button
                              onClick={commitFile}
                              disabled={!isDirty || !commitMsg.trim() || committing}
                              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:scale-105 active:scale-95 flex-shrink-0"
                              style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.5 0.18 260))' }}
                              title={!isDirty ? 'No changes' : !commitMsg.trim() ? 'Enter a commit message' : 'Commit to GitHub'}
                            >
                              {committing
                                ? <Loader2 className="w-3 h-3 animate-spin" />
                                : commitSuccess
                                  ? <CheckCheck className="w-3 h-3 text-emerald-300" />
                                  : <GitCommit className="w-3 h-3" />}
                              {commitSuccess ? 'Done!' : 'Commit'}
                            </button>
                          </div>
                        )}

                        {commitError && (
                          <p className="px-3 pb-2 text-[10px] text-red-400">{commitError}</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ══ DEPLOY TAB ══ */}
            {tab === 'deploy' && (
              <DeployTab selectedRepo={selectedRepo} vercelToken={vercelToken} />
            )}

            {/* ══ DATABASE TAB ══ */}
            {tab === 'database' && (
              <DatabaseTab supabaseUrl={supabaseUrl} supabaseKey={supabaseKey} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
