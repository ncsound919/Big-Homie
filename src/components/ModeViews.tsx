'use client';

import { useState, useCallback, useRef, useMemo } from 'react';
import {
  Globe, Search, Database, ArrowRight, ArrowLeft, Sparkles,
  BookOpen, FileText, Code2, BarChart3, Filter,
  Link2, Play, Table, Braces,
  Plus, X, Star, Download,
  Bookmark, History, Shield, Lock, MoreHorizontal,
  VolumeX, Share2,
  Camera, Home, RefreshCw,
  Mic, Wand2, FileDown, Trash2, ExternalLink,
  AlertTriangle, Loader2, Bug,
} from 'lucide-react';

/* ═══════════════════════════════════════════
   BROWSER TAB TYPES
   ═══════════════════════════════════════════ */
interface BrowserTab {
  id: string;
  title: string;
  url: string;
  favicon?: string;
  isActive: boolean;
  isLoading?: boolean;
  isMuted?: boolean;
  /** Navigation history for this tab */
  history: string[];
  /** Current position in history */
  historyIndex: number;
  /** Error when iframe fails to load */
  error?: string;
}

interface BookmarkItem {
  id: string;
  title: string;
  url: string;
  folder?: string;
}

interface HistoryEntry {
  id: string;
  title: string;
  url: string;
  visitedAt: string;
}

interface DownloadItem {
  id: string;
  name: string;
  size: string;
  progress: number;
  status: 'downloading' | 'complete' | 'failed';
}

type BrowserPanel = 'none' | 'bookmarks' | 'history' | 'downloads';

/* ── Helpers ── */
const QUICK_LINKS: { icon: typeof Globe; label: string; color: string; url: string }[] = [
  { icon: Globe, label: 'Google', color: 'text-blue-400', url: 'https://www.google.com/webhp?igu=1' },
  { icon: Code2, label: 'GitHub', color: 'text-foreground/80', url: 'https://github.com' },
  { icon: BookOpen, label: 'Wikipedia', color: 'text-emerald-400', url: 'https://en.m.wikipedia.org' },
  { icon: BarChart3, label: 'Analytics', color: 'text-orange-400', url: 'https://analytics.google.com' },
  { icon: FileText, label: 'Docs', color: 'text-cyan-400', url: 'https://developer.mozilla.org' },
  { icon: Search, label: 'DuckDuckGo', color: 'text-amber-400', url: 'https://duckduckgo.com' },
  { icon: Shield, label: 'Privacy', color: 'text-emerald-400', url: 'https://privacyguides.org' },
  { icon: Bug, label: 'Ladybird', color: 'text-rose-400', url: 'https://ladybird.org' },
];

function normalizeUrl(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return '';
  // If it looks like a URL (has dot and no spaces), add protocol
  if (/^[\w-]+(\.[\w-]+)+/.test(trimmed) && !trimmed.includes(' ')) {
    return `https://${trimmed}`;
  }
  // If already has protocol, use as-is
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  // Otherwise treat as a DuckDuckGo search
  return `https://duckduckgo.com/?q=${encodeURIComponent(trimmed)}`;
}

/** Wrap target URL through the server-side proxy to bypass X-Frame-Options. */
function proxyUrl(target: string): string {
  return `/api/proxy?url=${encodeURIComponent(target)}`;
}

function domainFromUrl(u: string): string {
  try {
    return new URL(u).hostname.replace(/^www\./, '');
  } catch {
    return u;
  }
}

function timeAgo(date: Date): string {
  const ms = Date.now() - date.getTime();
  const sec = Math.floor(ms / 1000);
  if (sec < 60) return 'Just now';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} min ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} hr ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

/* ═══════════════════════════════════════════
   BROWSE VIEW — FUNCTIONAL BROWSER
   ═══════════════════════════════════════════ */
export function BrowseView() {
  const [tabs, setTabs] = useState<BrowserTab[]>([
    { id: '1', title: 'New Tab', url: '', isActive: true, history: [], historyIndex: -1 },
  ]);
  const [urlInput, setUrlInput] = useState('');
  const [panel, setPanel] = useState<BrowserPanel>('none');
  const [showAISidebar, setShowAISidebar] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const [globalHistory, setGlobalHistory] = useState<HistoryEntry[]>([]);
  const urlInputRef = useRef<HTMLInputElement>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const activeTab = tabs.find(t => t.isActive);

  // Bookmarks stored in state so users can add to them
  const [bookmarks, setBookmarks] = useState<BookmarkItem[]>([
    { id: '1', title: 'GitHub', url: 'https://github.com', folder: 'Dev' },
    { id: '2', title: 'Stack Overflow', url: 'https://stackoverflow.com', folder: 'Dev' },
    { id: '3', title: 'Hacker News', url: 'https://news.ycombinator.com', folder: 'News' },
    { id: '4', title: 'Product Hunt', url: 'https://producthunt.com', folder: 'News' },
    { id: '5', title: 'Figma', url: 'https://figma.com', folder: 'Design' },
    { id: '6', title: 'Ladybird Browser', url: 'https://ladybird.org', folder: 'Dev' },
  ]);

  const [downloads] = useState<DownloadItem[]>([
    { id: '1', name: 'project-report.pdf', size: '2.4 MB', progress: 100, status: 'complete' },
    { id: '2', name: 'dataset.csv', size: '14.7 MB', progress: 67, status: 'downloading' },
  ]);

  const bookmarkFolders = useMemo(() => [...new Set(bookmarks.map(b => b.folder).filter(Boolean))] as string[], [bookmarks]);

  /* ── Navigation ── */
  const navigateTo = useCallback((rawUrl: string) => {
    const resolved = normalizeUrl(rawUrl);
    if (!resolved) return;
    setUrlInput(resolved);
    setTabs(prev => prev.map(t => {
      if (!t.isActive) return t;
      const newHistory = [...t.history.slice(0, t.historyIndex + 1), resolved];
      return {
        ...t,
        url: resolved,
        title: domainFromUrl(resolved),
        isLoading: true,
        error: undefined,
        history: newHistory,
        historyIndex: newHistory.length - 1,
      };
    }));
    // Add to global history
    setGlobalHistory(prev => [
      { id: Math.random().toString(36).slice(2), title: domainFromUrl(resolved), url: resolved, visitedAt: timeAgo(new Date()) },
      ...prev.slice(0, 49),
    ]);
  }, []);

  const goBack = useCallback(() => {
    if (!activeTab || activeTab.historyIndex <= 0) return;
    const prevUrl = activeTab.history[activeTab.historyIndex - 1];
    setUrlInput(prevUrl);
    setTabs(prev => prev.map(t => {
      if (!t.isActive) return t;
      return { ...t, url: prevUrl, title: domainFromUrl(prevUrl), historyIndex: t.historyIndex - 1, isLoading: true, error: undefined };
    }));
  }, [activeTab]);

  const goForward = useCallback(() => {
    if (!activeTab || activeTab.historyIndex >= activeTab.history.length - 1) return;
    const nextUrl = activeTab.history[activeTab.historyIndex + 1];
    setUrlInput(nextUrl);
    setTabs(prev => prev.map(t => {
      if (!t.isActive) return t;
      return { ...t, url: nextUrl, title: domainFromUrl(nextUrl), historyIndex: t.historyIndex + 1, isLoading: true, error: undefined };
    }));
  }, [activeTab]);

  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    if (!activeTab?.url) return;
    setReloadKey(k => k + 1);
    setTabs(prev => prev.map(t => t.isActive ? { ...t, isLoading: true, error: undefined } : t));
  }, [activeTab]);

  const goHome = useCallback(() => {
    setTabs(prev => prev.map(t => t.isActive ? { ...t, url: '', title: 'New Tab', isLoading: false, error: undefined } : t));
    setUrlInput('');
    urlInputRef.current?.focus();
  }, []);

  const handleUrlSubmit = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') navigateTo(urlInput);
  }, [urlInput, navigateTo]);

  const handleIframeLoad = useCallback(() => {
    setTabs(prev => prev.map(t => t.isActive ? { ...t, isLoading: false } : t));
  }, []);

  const handleIframeError = useCallback(() => {
    setTabs(prev => prev.map(t => t.isActive ? { ...t, isLoading: false, error: 'Page could not be loaded — the site may block embedding.' } : t));
  }, []);

  /* ── Tab management ── */
  const addTab = useCallback(() => {
    const id = Math.random().toString(36).slice(2, 9);
    setTabs(prev => [
      ...prev.map(t => ({ ...t, isActive: false })),
      { id, title: 'New Tab', url: '', isActive: true, history: [], historyIndex: -1 },
    ]);
    setUrlInput('');
    urlInputRef.current?.focus();
  }, []);

  const closeTab = useCallback((id: string) => {
    setTabs(prev => {
      if (prev.length <= 1) return prev;
      const filtered = prev.filter(t => t.id !== id);
      if (!filtered.some(t => t.isActive)) {
        filtered[filtered.length - 1].isActive = true;
      }
      return filtered;
    });
  }, []);

  const switchTab = useCallback((id: string) => {
    setTabs(prev => {
      const updated = prev.map(t => ({ ...t, isActive: t.id === id }));
      const active = updated.find(t => t.isActive);
      if (active) setUrlInput(active.url);
      return updated;
    });
  }, []);

  const togglePanel = useCallback((p: BrowserPanel) => {
    setPanel(prev => prev === p ? 'none' : p);
  }, []);

  const addBookmark = useCallback(() => {
    if (!activeTab?.url) return;
    const already = bookmarks.some(b => b.url === activeTab.url);
    if (already) return;
    setBookmarks(prev => [...prev, { id: Math.random().toString(36).slice(2), title: activeTab.title, url: activeTab.url, folder: 'Saved' }]);
  }, [activeTab, bookmarks]);

  const canGoBack = (activeTab?.historyIndex ?? 0) > 0;
  const canGoForward = activeTab ? activeTab.historyIndex < activeTab.history.length - 1 : false;
  const isOnPage = !!activeTab?.url;

  return (
    <div className="h-full flex flex-col">
      {/* ─── Tab Bar ─── */}
      <div className="flex-shrink-0 flex items-end gap-0 px-2 pt-1.5 bg-background/30 border-b border-border/20 overflow-x-auto scrollbar-none">
        {tabs.map(tab => (
          <div
            key={tab.id}
            onClick={() => switchTab(tab.id)}
            className={`group relative flex items-center gap-1.5 px-3 py-1.5 rounded-t-lg text-[11px] max-w-[180px] cursor-pointer transition-all ${
              tab.isActive
                ? 'bg-background/60 border border-b-0 border-border/30 text-foreground'
                : 'text-muted-foreground/60 hover:text-muted-foreground hover:bg-background/20'
            }`}
          >
            {tab.isLoading ? (
              <Loader2 className="w-3 h-3 flex-shrink-0 text-blue-400 animate-spin" />
            ) : (
              <Globe className="w-3 h-3 flex-shrink-0 text-blue-400" />
            )}
            <span className="truncate flex-1">{tab.title}</span>
            {tab.isMuted && <VolumeX className="w-2.5 h-2.5 text-muted-foreground/40" />}
            <button
              onClick={e => { e.stopPropagation(); closeTab(tab.id); }}
              className="p-0.5 rounded opacity-0 group-hover:opacity-100 hover:bg-muted/30 transition-all"
            >
              <X className="w-2.5 h-2.5" />
            </button>
          </div>
        ))}
        <button
          onClick={addTab}
          className="flex-shrink-0 p-1.5 rounded-lg text-muted-foreground/40 hover:text-muted-foreground hover:bg-background/20 transition-all mb-0.5"
          title="New tab"
        >
          <Plus className="w-3 h-3" />
        </button>
      </div>

      {/* ─── Navigation Bar ─── */}
      <div className="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 border-b border-border/20">
        <button
          onClick={goBack}
          disabled={!canGoBack}
          className={`p-1.5 rounded-lg transition-all ${canGoBack ? 'text-muted-foreground hover:text-foreground hover:bg-muted/10' : 'text-muted-foreground/20 cursor-not-allowed'}`}
          title="Back"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={goForward}
          disabled={!canGoForward}
          className={`p-1.5 rounded-lg transition-all ${canGoForward ? 'text-muted-foreground hover:text-foreground hover:bg-muted/10' : 'text-muted-foreground/20 cursor-not-allowed'}`}
          title="Forward"
        >
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={reload}
          disabled={!isOnPage}
          className={`p-1.5 rounded-lg transition-all ${isOnPage ? 'text-muted-foreground hover:text-foreground hover:bg-muted/10' : 'text-muted-foreground/20 cursor-not-allowed'}`}
          title="Reload"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${activeTab?.isLoading ? 'animate-spin' : ''}`} />
        </button>
        <button
          onClick={goHome}
          className="p-1.5 rounded-lg text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/10 transition-all"
          title="Home"
        >
          <Home className="w-3.5 h-3.5" />
        </button>

        {/* URL bar */}
        <div className="flex-1 flex items-center gap-2 px-3 py-1.5 rounded-full border border-border/30 bg-background/40 focus-within:border-blue-500/30 focus-within:ring-1 focus-within:ring-blue-500/10 transition-all">
          {isOnPage ? (
            <Lock className="w-3 h-3 text-emerald-400 flex-shrink-0" />
          ) : (
            <Search className="w-3 h-3 text-muted-foreground/40 flex-shrink-0" />
          )}
          <input
            ref={urlInputRef}
            type="text"
            value={urlInput}
            onChange={e => setUrlInput(e.target.value)}
            onKeyDown={handleUrlSubmit}
            placeholder="Search or enter URL..."
            className="flex-1 bg-transparent text-xs outline-none placeholder:text-muted-foreground/40"
          />
          {activeTab?.isLoading && <Loader2 className="w-3 h-3 text-blue-400 animate-spin flex-shrink-0" />}
          <Sparkles className="w-3 h-3 text-purple-400/60 flex-shrink-0" />
        </div>

        {/* Action buttons */}
        <button
          onClick={addBookmark}
          disabled={!isOnPage}
          className={`p-1.5 rounded-lg transition-all ${isOnPage ? 'text-muted-foreground/50 hover:text-yellow-400 hover:bg-yellow-500/10' : 'text-muted-foreground/20'}`}
          title={isOnPage ? 'Bookmark this page' : 'Bookmark'}
        >
          <Star className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => togglePanel('bookmarks')}
          className={`p-1.5 rounded-lg transition-all ${panel === 'bookmarks' ? 'bg-blue-500/10 text-blue-400' : 'text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/10'}`}
          title="Bookmarks"
        >
          <Bookmark className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => togglePanel('history')}
          className={`p-1.5 rounded-lg transition-all ${panel === 'history' ? 'bg-cyan-500/10 text-cyan-400' : 'text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/10'}`}
          title="History"
        >
          <History className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => togglePanel('downloads')}
          className={`p-1.5 rounded-lg transition-all ${panel === 'downloads' ? 'bg-emerald-500/10 text-emerald-400' : 'text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/10'}`}
          title="Downloads"
        >
          <Download className="w-3.5 h-3.5" />
        </button>
        <div className="w-px h-4 bg-border/20" />
        <button className="p-1.5 rounded-lg text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/10 transition-all" title="Screenshot">
          <Camera className="w-3.5 h-3.5" />
        </button>
        <button className="p-1.5 rounded-lg text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/10 transition-all" title="Share">
          <Share2 className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setShowAISidebar(v => !v)}
          className={`p-1.5 rounded-lg transition-all ${showAISidebar ? 'bg-purple-500/10 text-purple-400' : 'text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/10'}`}
          title="AI Assistant"
        >
          <Wand2 className="w-3.5 h-3.5" />
        </button>
        <button className="p-1.5 rounded-lg text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/10 transition-all" title="More">
          <MoreHorizontal className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* ─── Main Content Area ─── */}
      <div className="flex-1 flex overflow-hidden">
        {/* Side panel */}
        {panel !== 'none' && (
          <div className="w-64 flex-shrink-0 border-r border-border/20 bg-background/30 overflow-y-auto">
            {panel === 'bookmarks' && (
              <div className="p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold flex items-center gap-1.5"><Bookmark className="w-3 h-3 text-blue-400" /> Bookmarks</h3>
                  <button onClick={addBookmark} className="p-1 rounded hover:bg-muted/10" title="Bookmark current page"><Plus className="w-3 h-3 text-muted-foreground/50" /></button>
                </div>
                {bookmarkFolders.map(folder => (
                  <div key={folder}>
                    <p className="text-[10px] text-muted-foreground/60 uppercase tracking-wider mb-1.5">{folder}</p>
                    {bookmarks.filter(b => b.folder === folder).map(b => (
                      <button
                        key={b.id}
                        onClick={() => navigateTo(b.url)}
                        className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs text-left text-muted-foreground hover:text-foreground hover:bg-muted/10 transition-all"
                      >
                        <Globe className="w-3 h-3 text-blue-400/60 flex-shrink-0" />
                        <span className="truncate">{b.title}</span>
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            )}
            {panel === 'history' && (
              <div className="p-3 space-y-1">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-semibold flex items-center gap-1.5"><History className="w-3 h-3 text-cyan-400" /> History</h3>
                  <button onClick={() => setGlobalHistory([])} className="p-1 rounded hover:bg-muted/10" title="Clear history"><Trash2 className="w-3 h-3 text-muted-foreground/50" /></button>
                </div>
                {globalHistory.length === 0 && (
                  <p className="text-[10px] text-muted-foreground/40 text-center py-4">No history yet — start browsing!</p>
                )}
                {globalHistory.map(h => (
                  <button
                    key={h.id}
                    onClick={() => navigateTo(h.url)}
                    className="w-full flex items-start gap-2 px-2 py-2 rounded-lg text-left hover:bg-muted/10 transition-all"
                  >
                    <Globe className="w-3 h-3 text-cyan-400/50 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-foreground/80 truncate">{h.title}</p>
                      <p className="text-[10px] text-muted-foreground/50 truncate">{h.url}</p>
                    </div>
                    <span className="text-[9px] text-muted-foreground/40 flex-shrink-0 mt-0.5">{h.visitedAt}</span>
                  </button>
                ))}
              </div>
            )}
            {panel === 'downloads' && (
              <div className="p-3 space-y-2">
                <h3 className="text-xs font-semibold flex items-center gap-1.5 mb-2"><FileDown className="w-3 h-3 text-emerald-400" /> Downloads</h3>
                {downloads.map(d => (
                  <div key={d.id} className="px-2 py-2 rounded-lg border border-border/20 bg-background/20 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-foreground/80 truncate">{d.name}</p>
                        <p className="text-[10px] text-muted-foreground/50">{d.size}</p>
                      </div>
                      {d.status === 'complete' && <ExternalLink className="w-3 h-3 text-muted-foreground/40" />}
                    </div>
                    {d.status === 'downloading' && (
                      <div className="w-full h-1 rounded-full bg-muted/20 overflow-hidden">
                        <div className="h-full rounded-full bg-blue-500/60 transition-all" style={{ width: `${d.progress}%` }} />
                      </div>
                    )}
                    {d.status === 'complete' && (
                      <span className="text-[9px] text-emerald-400/80 font-medium">Complete</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Main browser viewport */}
        {activeTab?.url ? (
          <div className="flex-1 relative">
            {/* Loading bar */}
            {activeTab.isLoading && (
              <div className="absolute top-0 left-0 right-0 h-0.5 z-10 bg-blue-500/20 overflow-hidden">
                <div className="h-full w-1/3 bg-blue-500 animate-[loading-bar_1.5s_ease-in-out_infinite]" />
              </div>
            )}
            {/* Error overlay */}
            {activeTab.error ? (
              <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
                <div className="text-center space-y-3 max-w-sm px-6">
                  <div className="mx-auto w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                    <AlertTriangle className="w-6 h-6 text-amber-400" />
                  </div>
                  <h3 className="text-sm font-semibold text-foreground">Can&apos;t display this page</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{activeTab.error}</p>
                  <div className="flex items-center justify-center gap-2 pt-1">
                    <button onClick={() => { window.open(activeTab.url, '_blank', 'noopener,noreferrer'); }} className="px-3 py-1.5 rounded-lg text-[10px] font-medium bg-blue-500/10 border border-blue-500/30 text-blue-400 hover:bg-blue-500/20 transition-all">
                      Open in new window
                    </button>
                    <button onClick={goHome} className="px-3 py-1.5 rounded-lg text-[10px] font-medium bg-muted/10 border border-border/30 text-muted-foreground hover:bg-muted/20 transition-all">
                      Go home
                    </button>
                  </div>
                </div>
              </div>
            ) : null}
            <iframe
              ref={iframeRef}
              key={`${activeTab.id}-${reloadKey}`}
              src={proxyUrl(activeTab.url)}
              onLoad={handleIframeLoad}
              onError={handleIframeError}
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
              referrerPolicy="no-referrer"
              className="w-full h-full border-0"
              title={`Browser: ${activeTab.title}`}
            />
            <style>{`
              @keyframes loading-bar {
                0% { transform: translateX(-100%); }
                50% { transform: translateX(100%); }
                100% { transform: translateX(300%); }
              }
            `}</style>
          </div>
        ) : (
          /* ── New Tab homepage ── */
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center space-y-5 max-w-lg">
              <div className="mx-auto w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/15 flex items-center justify-center">
                <Globe className="w-9 h-9 text-blue-400" />
              </div>
              <h2 className="text-lg font-bold text-foreground">AgentBrowser</h2>
              <p className="text-sm text-muted-foreground leading-relaxed max-w-md mx-auto">
                AI-powered browsing with built-in automation. Type a URL, search with natural language,
                or let AI navigate for you.
              </p>

              {/* Quick links grid */}
              <div className="grid grid-cols-4 gap-3 max-w-sm mx-auto pt-2">
                {QUICK_LINKS.map(link => (
                  <button
                    key={link.label}
                    onClick={() => link.url && navigateTo(link.url)}
                    className="flex flex-col items-center gap-1.5 p-3 rounded-xl border border-border/20 bg-background/20 hover:bg-muted/10 hover:border-border/40 transition-all group"
                  >
                    <link.icon className={`w-5 h-5 ${link.color} group-hover:scale-110 transition-transform`} />
                    <span className="text-[10px] text-muted-foreground group-hover:text-foreground transition-colors">{link.label}</span>
                  </button>
                ))}
              </div>

              {/* Feature badges */}
              <div className="flex flex-wrap items-center justify-center gap-2 pt-3">
                {['Ad blocker', 'AI summarize', 'Auto-fill', 'Password vault', 'Tab groups', 'Reader mode', 'Screenshot'].map(feat => (
                  <span key={feat} className="px-2.5 py-1 rounded-full text-[10px] font-medium bg-blue-500/8 border border-blue-500/15 text-blue-400/80">{feat}</span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* AI Sidebar */}
        {showAISidebar && (
          <div className="w-72 flex-shrink-0 border-l border-border/20 bg-background/30 flex flex-col">
            <div className="p-3 border-b border-border/20 flex items-center justify-between">
              <h3 className="text-xs font-semibold flex items-center gap-1.5">
                <Wand2 className="w-3 h-3 text-purple-400" /> AI Assistant
              </h3>
              <button onClick={() => setShowAISidebar(false)} className="p-1 rounded hover:bg-muted/10">
                <X className="w-3 h-3 text-muted-foreground/50" />
              </button>
            </div>
            <div className="flex-1 p-4 flex items-center justify-center">
              <div className="text-center space-y-2">
                <Sparkles className="w-8 h-8 text-purple-400/40 mx-auto" />
                <p className="text-xs text-muted-foreground/60">Ask AI to summarize pages, fill forms, extract data, or navigate for you.</p>
              </div>
            </div>
            <div className="p-3 border-t border-border/20">
              <div className="flex items-center gap-2">
                <input
                  value={aiPrompt}
                  onChange={e => setAiPrompt(e.target.value)}
                  type="text"
                  placeholder="Ask AI anything..."
                  className="flex-1 px-3 py-2 rounded-lg border border-border/30 bg-background/20 text-xs outline-none focus:border-purple-500/30 transition-all placeholder:text-muted-foreground/40"
                />
                <button className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 hover:bg-purple-500/20 transition-all">
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   RESEARCH VIEW
   ═══════════════════════════════════════════ */
export function ResearchView() {
  const [query, setQuery] = useState('');
  const sources = [
    { id: 'web', icon: Globe, label: 'Web', active: true },
    { id: 'papers', icon: BookOpen, label: 'Papers', active: true },
    { id: 'code', icon: Code2, label: 'Code', active: false },
    { id: 'docs', icon: FileText, label: 'Docs', active: false },
  ];

  return (
    <div className="h-full flex flex-col">
      {/* Search bar + source toggles */}
      <div className="flex-shrink-0 p-4 border-b border-border/30 space-y-3">
        <div className="flex items-center gap-2 max-w-3xl mx-auto">
          <div className="flex-1 flex items-center gap-2 px-4 py-2.5 rounded-xl border border-border/40 bg-background/40 focus-within:border-cyan-500/40 focus-within:ring-1 focus-within:ring-cyan-500/20 transition-all">
            <Search className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Research any topic with multi-source AI..."
              className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground/50"
            />
          </div>
          <button className="px-4 py-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold hover:bg-cyan-500/20 transition-all flex items-center gap-1.5">
            <Search className="w-3.5 h-3.5" /> Research
          </button>
        </div>
        <div className="flex items-center gap-2 max-w-3xl mx-auto">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Sources:</span>
          {sources.map(s => (
            <button
              key={s.id}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-medium transition-all ${
                s.active
                  ? 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-400'
                  : 'border border-border/30 text-muted-foreground/60 hover:text-muted-foreground'
              }`}
            >
              <s.icon className="w-3 h-3" /> {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results area */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center space-y-4 max-w-md">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
            <Search className="w-7 h-7 text-cyan-400" />
          </div>
          <h2 className="text-lg font-bold text-foreground">Deep Research Mode</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Query multiple sources simultaneously — web, academic papers, code repositories, and documentation.
            AI synthesizes findings into structured reports.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
            {['Multi-source search', 'AI synthesis', 'Citation tracking', 'Export reports', 'Knowledge graph'].map(feat => (
              <span key={feat} className="px-2.5 py-1 rounded-full text-[10px] font-medium bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">{feat}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   SCRAPE VIEW
   ═══════════════════════════════════════════ */
export function ScrapeView() {
  const [targetUrl, setTargetUrl] = useState('');

  return (
    <div className="h-full flex flex-col">
      {/* Target config */}
      <div className="flex-shrink-0 p-4 border-b border-border/30 space-y-3">
        <div className="flex items-center gap-2 max-w-3xl mx-auto">
          <div className="flex-1 flex items-center gap-2 px-4 py-2.5 rounded-xl border border-border/40 bg-background/40 focus-within:border-orange-500/40 focus-within:ring-1 focus-within:ring-orange-500/20 transition-all">
            <Link2 className="w-4 h-4 text-orange-400 flex-shrink-0" />
            <input
              type="url"
              value={targetUrl}
              onChange={e => setTargetUrl(e.target.value)}
              placeholder="Enter target URL for data extraction..."
              className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground/50"
            />
          </div>
          <button className="px-4 py-2.5 rounded-xl bg-orange-500/10 border border-orange-500/30 text-orange-400 text-xs font-semibold hover:bg-orange-500/20 transition-all flex items-center gap-1.5">
            <Play className="w-3.5 h-3.5" /> Extract
          </button>
        </div>
        <div className="flex items-center gap-2 max-w-3xl mx-auto">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Output:</span>
          {[
            { icon: Table, label: 'Table' },
            { icon: Braces, label: 'JSON' },
            { icon: BarChart3, label: 'Charts' },
            { icon: Filter, label: 'Filtered' },
          ].map(o => (
            <button
              key={o.label}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-medium border border-border/30 text-muted-foreground/60 hover:text-muted-foreground hover:border-orange-500/20 transition-all"
            >
              <o.icon className="w-3 h-3" /> {o.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content area */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center space-y-4 max-w-md">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
            <Database className="w-7 h-7 text-orange-400" />
          </div>
          <h2 className="text-lg font-bold text-foreground">Data Extraction Pipeline</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Extract structured data from any website using Firecrawl, Maxun self-healing selectors,
            and Skyvern vision-based detection. Output as JSON, CSV, or feed into your pipeline.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
            {['Self-healing selectors', 'Pagination handling', 'Anti-detection', 'Scheduled runs', 'API output'].map(feat => (
              <span key={feat} className="px-2.5 py-1 rounded-full text-[10px] font-medium bg-orange-500/10 border border-orange-500/20 text-orange-400">{feat}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
