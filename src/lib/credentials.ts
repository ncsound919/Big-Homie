// Client-side credential manager.
// Tokens are stored in localStorage only — never persisted server-side.
// They are sent as Bearer tokens over HTTPS to local proxy API routes only.

export interface Credentials {
  githubToken: string;
  vercelToken: string;
  supabaseUrl: string;
  supabaseKey: string;
}

const STORAGE_KEY = 'ab_credentials';

const DEFAULTS: Credentials = {
  githubToken: '',
  vercelToken: '',
  supabaseUrl: '',
  supabaseKey: '',
};

export function getCredentials(): Credentials {
  if (typeof window === 'undefined') return { ...DEFAULTS };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULTS };
    return { ...DEFAULTS, ...(JSON.parse(raw) as Partial<Credentials>) };
  } catch {
    return { ...DEFAULTS };
  }
}

export function saveCredentials(creds: Credentials): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(creds));
  window.dispatchEvent(new CustomEvent('ab:credentials-changed'));
}

export function clearCredentials(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new CustomEvent('ab:credentials-changed'));
}

export function hasGitHubToken(): boolean {
  return getCredentials().githubToken.length > 10;
}
