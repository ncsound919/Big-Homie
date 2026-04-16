import { afterEach, describe, expect, it, vi } from 'vitest';
import { GET } from '@/app/api/route';

describe('stars proxy route', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('rejects requests without repos', async () => {
    const response = await GET(new Request('http://localhost/api'));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ error: 'Missing repos parameter' });
  });

  it('rejects requests without valid repos', async () => {
    const response = await GET(new Request('http://localhost/api?repos=bad repo,still bad'));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ error: 'No valid repos provided' });
  });

  it('returns star data for valid repositories', async () => {
    const fetchMock = vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ stargazers_count: 42, forks_count: 7, open_issues_count: 3 }),
    } as Response);

    const response = await GET(new Request('http://localhost/api?repos=vercel/next.js,invalid repo'));
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.stars['vercel/next.js']).toEqual({ stars: 42, forks: 7, issues: 3 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});