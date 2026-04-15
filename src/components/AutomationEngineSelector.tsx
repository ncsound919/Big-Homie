'use client';

import { AppIcon } from '@/lib/icons';
import { Star, TrendingUp } from 'lucide-react';

export interface EngineOption {
  id: string;
  name: string;
  icon: string;
  color: string;
  desc: string;
  browsers: string[];
  bestFor: string;
  trending?: boolean;
  stars?: string;
}

const ENGINES: EngineOption[] = [
  {
    id: 'browser-use',
    name: 'browser-use',
    icon: 'brain',
    color: 'text-pink-500',
    desc: '#1 AI browser automation — 86k+ stars, natural language control',
    browsers: ['Chromium', 'Firefox', 'WebKit'],
    bestFor: 'LLM-driven automation & stealth',
    trending: true,
    stars: '86k',
  },
  {
    id: 'playwright',
    name: 'Playwright',
    icon: 'monitor',
    color: 'text-green-400',
    desc: 'Cross-browser with auto-wait and network interception',
    browsers: ['Chromium', 'Firefox', 'WebKit'],
    bestFor: 'Cross-browser testing & automation',
  },
  {
    id: 'puppeteer',
    name: 'Puppeteer',
    icon: 'mouse-pointer',
    color: 'text-cyan-400',
    desc: 'Fast Chromium control via Chrome DevTools Protocol',
    browsers: ['Chromium'],
    bestFor: 'Scraping, PDFs & screenshots',
  },
  {
    id: 'selenium',
    name: 'Selenium',
    icon: 'globe',
    color: 'text-blue-400',
    desc: 'Universal browser support with multi-language bindings',
    browsers: ['Chrome', 'Firefox', 'Safari', 'Edge'],
    bestFor: 'Enterprise & legacy browser testing',
  },
  {
    id: 'skyvern',
    name: 'Skyvern AI',
    icon: 'eye',
    color: 'text-purple-400',
    desc: 'LLM + computer vision — 21k+ stars, no selectors needed',
    browsers: ['Any (vision-based)'],
    bestFor: 'Adaptive automation & CAPTCHA solving',
    trending: true,
    stars: '21k',
  },
  {
    id: 'stagehand',
    name: 'Stagehand',
    icon: 'wand',
    color: 'text-indigo-400',
    desc: 'Next-gen orchestration for AI-controlled browsers',
    browsers: ['Chromium', 'Firefox'],
    bestFor: 'Multi-agent workflow orchestration',
    trending: true,
    stars: '12k',
  },
];

interface AutomationEngineSelectorProps {
  selectedEngine: string;
  onSelect: (engineId: string) => void;
}

export default function AutomationEngineSelector({ selectedEngine, onSelect }: AutomationEngineSelectorProps) {
  return (
    <div>
      <label className="text-sm font-medium text-foreground mb-3 block">
        <AppIcon name="bolt" className="inline-block w-3.5 h-3.5 mr-1.5 text-primary" />
        Automation Engine
        <span className="ml-2 inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-medium bg-pink-500/10 text-pink-400 border border-pink-500/20">
          <TrendingUp className="w-2 h-2" />
          2025 Trending
        </span>
      </label>
      <div className="grid grid-cols-2 gap-2">
        {ENGINES.map(engine => (
          <button
            key={engine.id}
            type="button"
            onClick={() => onSelect(engine.id)}
            className={`p-3 rounded-xl border text-left transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] ${
              selectedEngine === engine.id
                ? 'border-primary/50 bg-primary/10 shadow-sm glow-purple'
                : engine.trending
                ? 'border-pink-500/30 bg-pink-500/5 hover:border-pink-500/40 hover:bg-pink-500/10'
                : 'border-border/50 bg-background/30 hover:border-primary/30 hover:bg-primary/5'
            }`}
          >
            <div className="flex items-center gap-2 mb-1.5">
              <AppIcon name={engine.icon} className={`w-4 h-4 ${engine.color}`} />
              <span className="text-xs font-semibold text-foreground">{engine.name}</span>
              {engine.stars && (
                <span className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded text-[8px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 ml-auto">
                  <Star className="w-2 h-2" />
                  {engine.stars}
                </span>
              )}
            </div>
            <p className="text-[10px] text-muted-foreground leading-snug mb-2">{engine.desc}</p>
            <div className="flex flex-wrap gap-1">
              {engine.browsers.map(b => (
                <span key={b} className="px-1.5 py-0.5 rounded text-[8px] font-medium bg-muted/30 text-muted-foreground border border-border/20">
                  {b}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
