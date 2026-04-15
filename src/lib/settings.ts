// App-wide settings stored in localStorage.
// Separate from credentials (tokens) — this holds preferences and configuration.

export type AppMode = 'easy' | 'dev';
export type ModelProvider = 'cloud' | 'local';

export interface LocalModelConfig {
  provider: 'ollama' | 'lmstudio' | 'llamacpp' | 'custom';
  endpoint: string;
  modelName: string;
  apiKey: string; // optional for local, needed for custom
}

export interface CustomAgent {
  id: string;
  name: string;
  description: string;
  /** Base64 content or URL to agent config file */
  config: string;
  fileName: string;
  enabled: boolean;
  addedAt: string;
}

export interface IntegrationConfig {
  id: string;
  name: string;
  enabled: boolean;
  apiKey: string;
  /** Which pipeline phase(s) this integration hooks into */
  phases: number[];
}

export type SecurityLevel = 'passive' | 'active' | 'configurable';

export interface AppSettings {
  mode: AppMode;
  modelProvider: ModelProvider;
  localModel: LocalModelConfig;
  customAgents: CustomAgent[];
  integrations: IntegrationConfig[];
  pipeline: {
    autoFix: boolean;
    skipAudit: boolean;
    parallelPhases: boolean;
    defaultSpeed: number;
  };
  security: {
    level: SecurityLevel;
  };
  ui: {
    particles: boolean;
    animations: boolean;
    compactView: boolean;
    showTechDetails: boolean;
  };
}

const STORAGE_KEY = 'ab_settings';

export const DEFAULT_INTEGRATIONS: IntegrationConfig[] = [
  // CI/CD & Hosting
  { id: 'vercel', name: 'Vercel', enabled: false, apiKey: '', phases: [12] },
  { id: 'netlify', name: 'Netlify', enabled: false, apiKey: '', phases: [12] },
  { id: 'railway', name: 'Railway', enabled: false, apiKey: '', phases: [4, 12] },
  // Databases
  { id: 'supabase', name: 'Supabase', enabled: false, apiKey: '', phases: [4, 6] },
  { id: 'neon', name: 'Neon Postgres', enabled: false, apiKey: '', phases: [4, 6] },
  { id: 'planetscale', name: 'PlanetScale', enabled: false, apiKey: '', phases: [4, 6] },
  { id: 'turso', name: 'Turso (libSQL)', enabled: false, apiKey: '', phases: [4, 6] },
  // AI / LLM
  { id: 'openai', name: 'OpenAI', enabled: false, apiKey: '', phases: [1, 8] },
  { id: 'anthropic', name: 'Anthropic', enabled: false, apiKey: '', phases: [1, 8] },
  { id: 'groq', name: 'Groq', enabled: false, apiKey: '', phases: [1, 8] },
  // Monitoring & Analytics
  { id: 'sentry', name: 'Sentry', enabled: false, apiKey: '', phases: [10, 12] },
  { id: 'posthog', name: 'PostHog', enabled: false, apiKey: '', phases: [10, 12] },
  // Auth
  { id: 'clerk', name: 'Clerk', enabled: false, apiKey: '', phases: [6] },
  { id: 'auth0', name: 'Auth0', enabled: false, apiKey: '', phases: [6] },
  // Payments
  { id: 'stripe', name: 'Stripe', enabled: false, apiKey: '', phases: [6, 9] },
  { id: 'lemonsqueezy', name: 'Lemon Squeezy', enabled: false, apiKey: '', phases: [6, 9] },
  // Email
  { id: 'resend', name: 'Resend', enabled: false, apiKey: '', phases: [9] },
  { id: 'sendgrid', name: 'SendGrid', enabled: false, apiKey: '', phases: [9] },
  // Storage
  { id: 'cloudflare-r2', name: 'Cloudflare R2', enabled: false, apiKey: '', phases: [4, 9] },
  { id: 'uploadthing', name: 'UploadThing', enabled: false, apiKey: '', phases: [9] },
];

const DEFAULTS: AppSettings = {
  mode: 'easy',
  modelProvider: 'cloud',
  localModel: {
    provider: 'ollama',
    endpoint: 'http://localhost:11434',
    modelName: 'llama3.1',
    apiKey: '',
  },
  customAgents: [],
  integrations: DEFAULT_INTEGRATIONS,
  pipeline: {
    autoFix: true,
    skipAudit: false,
    parallelPhases: false,
    defaultSpeed: 1,
  },
  security: {
    level: 'active' as SecurityLevel,
  },
  ui: {
    particles: true,
    animations: true,
    compactView: false,
    showTechDetails: false,
  },
};

export function getSettings(): AppSettings {
  if (typeof window === 'undefined') return structuredClone(DEFAULTS);
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return structuredClone(DEFAULTS);
    const parsed = JSON.parse(raw) as Partial<AppSettings>;
    // Deep merge with defaults so new fields are always present
    return {
      ...DEFAULTS,
      ...parsed,
      localModel: { ...DEFAULTS.localModel, ...(parsed.localModel ?? {}) },
      pipeline: { ...DEFAULTS.pipeline, ...(parsed.pipeline ?? {}) },
      security: { ...DEFAULTS.security, ...(parsed.security ?? {}) },
      ui: { ...DEFAULTS.ui, ...(parsed.ui ?? {}) },
      integrations: parsed.integrations?.length ? parsed.integrations : DEFAULTS.integrations,
      customAgents: parsed.customAgents ?? [],
    };
  } catch {
    return structuredClone(DEFAULTS);
  }
}

export function saveSettings(settings: AppSettings): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  window.dispatchEvent(new CustomEvent('ab:settings-changed', { detail: settings }));
}

export function getEnabledIntegrations(phaseId?: number): IntegrationConfig[] {
  const settings = getSettings();
  return settings.integrations.filter(i =>
    i.enabled && i.apiKey.length > 0 && (phaseId === undefined || i.phases.includes(phaseId))
  );
}

export function getActiveAgents(): CustomAgent[] {
  return getSettings().customAgents.filter(a => a.enabled);
}
