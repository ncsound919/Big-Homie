'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export interface ToastItem {
  id: string;
  title: string;
  description?: string;
  variant?: 'default' | 'success' | 'warning' | 'error';
  duration?: number;
}

interface ToastContextType {
  toasts: ToastItem[];
  addToast: (toast: Omit<ToastItem, 'id'>) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const addToast = useCallback((toast: Omit<ToastItem, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { ...toast, id }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, toast.duration || 4000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
}

function ToastContainer({ toasts, removeToast }: { toasts: ToastItem[]; removeToast: (id: string) => void }) {
  const variantStyles = {
    default: 'border-border/50 glass-strong',
    success: 'border-emerald-500/30 bg-emerald-500/10',
    warning: 'border-amber-500/30 bg-amber-500/10',
    error: 'border-red-500/30 bg-red-500/10',
  };

  const variantIcons = {
    default: 'fa-circle-info',
    success: 'fa-circle-check',
    warning: 'fa-triangle-exclamation',
    error: 'fa-circle-xmark',
  };

  const variantIconColors = {
    default: 'text-primary',
    success: 'text-emerald-400',
    warning: 'text-amber-400',
    error: 'text-red-400',
  };

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast, index) => (
        <div
          key={toast.id}
          className={`pointer-events-auto rounded-lg border p-3 shadow-lg animate-slide-in-right ${variantStyles[toast.variant || 'default']}`}
          style={{ animationDelay: `${index * 50}ms` }}
        >
          <div className="flex items-start gap-2.5">
            <i className={`fa-solid ${variantIcons[toast.variant || 'default']} ${variantIconColors[toast.variant || 'default']} mt-0.5 text-sm`} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground">{toast.title}</p>
              {toast.description && (
                <p className="text-xs text-muted-foreground mt-0.5">{toast.description}</p>
              )}
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-muted-foreground hover:text-foreground transition-colors p-0.5"
              aria-label="Dismiss"
            >
              <i className="fa-solid fa-xmark text-xs" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
