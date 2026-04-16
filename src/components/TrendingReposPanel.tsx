'use client';

import { useState, useEffect } from 'react';
import { AppIcon } from '@/lib/icons';
import { TRENDING_REPOS, getTotalStars, formatStars, type TrendingRepoData } from '@/lib/trending-repos';
import { Star, TrendingUp, ExternalLink, GitFork, ArrowUpRight, RefreshCw } from 'lucide-react';

const CATEGORIES = [
  { id: 'all' as const, label: 'All', icon: 'layers', color: 'text-primary' },
  { id: 'browser' as const, label: 'Browser Automation', icon: 'monitor', color: 'text-pink-400' },
  { id: 'agent' as const, label: 'AI Coding Agents', icon: 'bot', color: 'text-amber-400' },
  { id: 'orchestration' as const, label: 'Orchestration', icon: 'git-branch', color: 'text-teal-400' },
];

const CATEGORY_COLORS: Record<TrendingRepoData['category'] | 'all', { card: string; badge: string; tag: string; icon: string }> = {
  all:           { card: 'border-primary/20 bg-primary/5 hover:border-primary/40 hover:bg-primary/10',         badge: 'bg-primary/10 text-primary border-primary/20',           tag: 'bg-primary/10 text-primary border-primary/20',         icon: 'bg-primary/10' },
  browser:       { card: 'border-pink-500/20 bg-pink-500/5 hover:border-pink-500/40 hover:bg-pink-500/10',     badge: 'bg-pink-500/10 text-pink-400 border-pink-500/20',         tag: 'bg-pink-500/10 text-pink-400 border-pink-500/20',       icon: 'bg-pink-500/10' },
  agent:         { card: 'border-amber-500/20 bg-amber-500/5 hover:border-amber-500/40 hover:bg-amber-500/10', badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20',       tag: 'bg-amber-500/10 text-amber-400 border-amber-500/20',     icon: 'bg-amber-500/10' },
  orchestration: { card: 'border-teal-500/20 bg-teal-500/5 hover:border-teal-500/40 hover:bg-teal-500/10',    badge: 'bg-teal-500/10 text-teal-400 border-teal-500/20',         tag: 'bg-teal-500/10 text-teal-400 border-teal-500/20',       icon: 'bg-teal-500/10' },
};

type CategoryFilter = 'all' | TrendingRepoData['category'];

// Top repos with a GitHub path for live star fetching
const LIVE_REPOS = TRENDING_REPOS.filter(r => r.repo).slice(0, 8).map(r => r.repo as string);

export default function TrendingReposPanel() {
  const [filter, setFilter] = useState<CategoryFilter>('all');
  const [liveStars, setLiveStars] = useState<Record<string, number>>({});
  const [isFetching, setIsFetching] = useState(false);

  useEffect(() => {
    const fetchLiveStars = async () => {
      if (LIVE_REPOS.length === 0) return;
      setIsFetching(true);
      try {
        const res = await fetch(`/api?repos=${encodeURIComponent(LIVE_REPOS.join(','))}`);
        if (res.ok) {
          const data = await res.json() as { stars: Record<string, { stars: number }> };
          const mapped: Record<string, number> = {};
          for (const [repo, info] of Object.entries(data.stars)) {
            mapped[repo] = info.stars;
          }
          setLiveStars(mapped);
        }
      } catch {
        // silently fall back to static data
      } finally {
        setIsFetching(false);
      }
    };
    fetchLiveStars();
  }, []);

  const filtered = filter === 'all' ? TRENDING_REPOS : TRENDING_REPOS.filter(r => r.category === filter);
  const totalStars = getTotalStars(TRENDING_REPOS);

  return (
    <div className="w-full rounded-2xl border border-border/30 bg-background/20 overflow-hidden">
      {/* Header */}
      <div className="px-4 sm:px-6 py-4 border-b border-border/30">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-pink-400" />
            <h3 className="text-sm font-bold text-foreground">Trending GitHub Repos 2026</h3>
            {isFetching && <RefreshCw className="w-3 h-3 text-muted-foreground/50 animate-spin" />}
            {!isFetching && Object.keys(liveStars).length > 0 && (
              <span className="text-[8px] font-medium text-emerald-400 border border-emerald-500/20 bg-emerald-500/10 px-1.5 py-0.5 rounded-full">live</span>
            )}
          </div>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-[9px] font-bold text-amber-400">
            <Star className="w-2.5 h-2.5" />
            {Math.round(totalStars / 1000)}k+ Total Stars
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          Top open-source projects powering the next generation of AI browser automation and coding agents.
        </p>
      </div>

      {/* Category Filter */}
      <div className="px-4 sm:px-6 py-3 border-b border-border/20 flex flex-wrap gap-2">
        {CATEGORIES.map(cat => (
          <button
            key={cat.id}
            onClick={() => setFilter(cat.id)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all duration-200 hover:scale-105 active:scale-95 ${
              filter === cat.id
                ? 'bg-primary/15 text-primary border border-primary/30'
                : 'bg-muted/30 text-muted-foreground border border-transparent hover:border-border/40 hover:text-foreground'
            }`}
          >
            <AppIcon name={cat.icon} className={`w-3 h-3 ${filter === cat.id ? 'text-primary' : cat.color}`} />
            {cat.label}
          </button>
        ))}
      </div>

      {/* Repos Grid */}
      <div className="px-4 sm:px-6 py-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-[520px] overflow-y-auto">
        {filtered.map(repo => {
          const colors = CATEGORY_COLORS[repo.category] ?? CATEGORY_COLORS.browser;
          return (
            <a
              key={repo.name}
              href={`https://github.com/${repo.repo}`}
              target="_blank"
              rel="noopener noreferrer"
              className={`group p-3 rounded-xl border transition-all duration-200 hover:scale-[1.02] active:scale-[0.99] ${colors.card}`}
            >
              <div className="flex items-start gap-2.5">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${colors.icon}`}>
                  <AppIcon name={repo.icon} className={`w-4 h-4 ${repo.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-xs font-semibold text-foreground">{repo.name}</span>
                    <span className={`inline-flex items-center gap-0.5 px-1 py-0.5 rounded text-[8px] font-medium border ${colors.badge}`}>
                      <Star className="w-2 h-2" />
                      {formatStars(liveStars[repo.repo ?? ''] ?? repo.stars)}
                    </span>
                    <ArrowUpRight className="w-3 h-3 text-muted-foreground/40 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <p className="text-[10px] text-muted-foreground leading-snug mt-0.5 line-clamp-2">
                    {repo.description}
                  </p>
                </div>
              </div>

              {/* Highlights */}
              <div className="mt-2 flex flex-wrap gap-1">
                {repo.highlights.map((h, i) => (
                  <span key={i} className={`px-1.5 py-0.5 rounded text-[8px] font-medium border ${colors.tag}`}>
                    {h}
                  </span>
                ))}
              </div>

              {/* Repo path */}
              <div className="mt-2 flex items-center gap-1 text-[9px] text-muted-foreground/60">
                <GitFork className="w-2.5 h-2.5" />
                <span className="truncate">{repo.repo}</span>
              </div>
            </a>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-4 sm:px-6 py-3 border-t border-border/20 flex items-center justify-between flex-wrap gap-2">
        <span className="text-[10px] text-muted-foreground">
          {filtered.length} repositories · Updated April 2026
        </span>
        <a
          href="https://github.com/topics/browser-automation"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-[10px] text-pink-400 hover:text-pink-300 transition-colors"
        >
          <ExternalLink className="w-2.5 h-2.5" />
          Explore more on GitHub
        </a>
      </div>
    </div>
  );
}
