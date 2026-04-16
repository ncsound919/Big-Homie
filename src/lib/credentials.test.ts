import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  clearCredentials,
  getCredentials,
  hasGitHubToken,
  saveCredentials,
} from '@/lib/credentials';

describe('credentials store', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('returns defaults when storage is empty or invalid', () => {
    expect(getCredentials()).toEqual({
      githubToken: '',
      vercelToken: '',
      supabaseUrl: '',
      supabaseKey: '',
    });

    localStorage.setItem('ab_credentials', '{bad json');
    expect(getCredentials().githubToken).toBe('');
  });

  it('saves and clears credentials while notifying listeners', () => {
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent');

    saveCredentials({
      githubToken: 'ghp_12345678901',
      vercelToken: 'vercel-token',
      supabaseUrl: 'https://example.supabase.co',
      supabaseKey: 'supabase-key',
    });

    expect(getCredentials().vercelToken).toBe('vercel-token');

    clearCredentials();

    expect(getCredentials().githubToken).toBe('');
    expect(dispatchSpy).toHaveBeenCalledTimes(2);
  });

  it('detects whether a usable github token exists', () => {
    expect(hasGitHubToken()).toBe(false);

    saveCredentials({
      githubToken: 'ghp_12345678901',
      vercelToken: '',
      supabaseUrl: '',
      supabaseKey: '',
    });

    expect(hasGitHubToken()).toBe(true);
  });
});