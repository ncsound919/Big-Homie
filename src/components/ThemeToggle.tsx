'use client';

import { useTheme } from 'next-themes';
import { Moon, Sun } from 'lucide-react';
import { useSyncExternalStore } from 'react';

function subscribeToHydration() {
  return () => {};
}

export default function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const mounted = useSyncExternalStore(subscribeToHydration, () => true, () => false);

  // Until mounted, render a neutral placeholder that matches the server output
  // exactly — prevents the client/server class mismatch
  if (!mounted) {
    return (
      <div
        className="relative w-14 h-7 rounded-full"
        style={{ background: 'linear-gradient(135deg, oklch(0.25 0.04 280), oklch(0.2 0.03 260))' }}
        aria-hidden="true"
      />
    );
  }

  const isDark = resolvedTheme === 'dark';

  const toggle = () => setTheme(isDark ? 'light' : 'dark');

  return (
    <button
      onClick={toggle}
      className="relative w-14 h-7 rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary/50 hover:scale-105 active:scale-95"
      style={{
        background: isDark
          ? 'linear-gradient(135deg, oklch(0.25 0.04 280), oklch(0.2 0.03 260))'
          : 'linear-gradient(135deg, oklch(0.85 0.08 80), oklch(0.9 0.06 60))',
      }}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <span
        className={`absolute top-0.5 w-6 h-6 rounded-full flex items-center justify-center transition-all duration-300 ${
          isDark ? 'left-[calc(100%-1.625rem)]' : 'left-0.5'
        }`}
        style={{ background: isDark ? 'oklch(0.25 0.04 280)' : 'white' }}
      >
        {isDark ? (
          <Moon className="w-3 h-3 text-yellow-300" />
        ) : (
          <Sun className="w-3 h-3 text-amber-500" />
        )}
      </span>
    </button>
  );
}

