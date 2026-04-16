'use client';

import { useState, useRef, useEffect } from 'react';
import { AppIcon } from '@/lib/icons';
import { Search, Inbox, ChevronRight } from 'lucide-react';

export interface LogEntry {
  id: string;
  time: string;
  text: string;
  /** Icon name key for AppIcon (e.g. 'check', 'wrench', 'shield') */
  icon: string;
  color: string;
  category: 'build' | 'audit' | 'fix' | 'deploy' | 'info' | 'security';
  detail?: string;
}

interface ActivityLogProps {
  entries: LogEntry[];
}

const categoryConfig = {
  build: { label: 'Build', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
  audit: { label: 'Audit', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
  fix: { label: 'Fix', color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' },
  deploy: { label: 'Deploy', color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20' },
  info: { label: 'Info', color: 'text-muted-foreground', bg: 'bg-muted/20', border: 'border-border/30' },
  security: { label: 'Security', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
};

type Category = keyof typeof categoryConfig;

export default function ActivityLog({ entries }: ActivityLogProps) {
  const [filter, setFilter] = useState<Category | 'all'>('all');
  const [search, setSearch] = useState('');
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const scrollRef = useRef<HTMLDivElement>(null);

  const filtered = entries.filter(e => {
    if (filter !== 'all' && e.category !== filter) return false;
    if (search && !e.text.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [filtered.length]);

  return (
    <div className="rounded-xl border border-border/30 bg-background/20 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border/30 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AppIcon name="list" className="w-4 h-4 text-primary" />
          <span className="text-sm font-semibold">Activity Log</span>
          <span className="text-[10px] text-muted-foreground font-mono">({entries.length})</span>
        </div>
      </div>

      {/* Filter bar */}
      <div className="px-4 py-2 border-b border-border/20 flex flex-wrap items-center gap-2">
        <div className="flex gap-1 flex-wrap">
          {(['all', 'build', 'audit', 'fix', 'deploy', 'info'] as const).map(cat => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-2 py-0.5 rounded text-[10px] font-medium transition-all duration-200 ${
                filter === cat
                  ? cat === 'all'
                    ? 'bg-primary/20 text-primary border border-primary/30'
                    : `${categoryConfig[cat].bg} ${categoryConfig[cat].color} border ${categoryConfig[cat].border}`
                  : 'bg-muted/30 text-muted-foreground border border-transparent hover:bg-muted/50'
              }`}
            >
              {cat === 'all' ? 'All' : categoryConfig[cat].label}
            </button>
          ))}
        </div>
        <div className="flex-1 min-w-[120px] max-w-[200px] ml-auto">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-2.5 h-2.5 text-muted-foreground/50" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search logs..."
              className="w-full pl-6 pr-2 py-1 rounded-md border border-border/30 bg-background/30 text-[10px] text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-primary/30"
            />
          </div>
        </div>
      </div>

      {/* Log body */}
      <div ref={scrollRef} className="max-h-[280px] overflow-y-auto px-3 py-2 space-y-0.5">
        {filtered.length === 0 ? (
          <div className="py-6 text-center text-xs text-muted-foreground/50">
            <Inbox className="w-5 h-5 mx-auto mb-1" />
            No matching log entries
          </div>
        ) : (
          filtered.map(entry => {
            const isExpanded = expandedIds.has(entry.id);
            const cat = categoryConfig[entry.category];
            return (
              <div key={entry.id} className="group">
                <button
                  onClick={() => entry.detail ? toggleExpand(entry.id) : undefined}
                  className={`w-full flex items-start gap-2 py-1.5 px-1 rounded-md transition-all duration-150 hover:bg-background/40 ${entry.detail ? 'cursor-pointer' : 'cursor-default'}`}
                >
                  <span className="text-[9px] font-mono text-muted-foreground/50 min-w-[38px] pt-0.5 flex-shrink-0">
                    {entry.time}
                  </span>
                  <span className={`w-4 h-4 rounded flex items-center justify-center flex-shrink-0 ${cat.bg} ${cat.color}`}>
                    <AppIcon name={entry.icon} className="w-2.5 h-2.5" />
                  </span>
                  <span className="text-[11px] text-foreground/80 leading-tight text-left flex-1 min-w-0">
                    {entry.text}
                  </span>
                  {entry.detail && (
                    <ChevronRight className={`w-2.5 h-2.5 text-muted-foreground/40 transition-transform duration-200 flex-shrink-0 mt-0.5 ${isExpanded ? 'rotate-90' : ''}`} />
                  )}
                </button>
                {isExpanded && entry.detail && (
                  <div className="ml-[48px] mb-1 p-2 rounded-md bg-background/30 border border-border/20 text-[10px] text-muted-foreground font-mono leading-relaxed animate-fade-in-up">
                    {entry.detail}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
