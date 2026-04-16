import { afterEach, describe, expect, it, vi } from 'vitest';
import { GET, POST } from '@/app/api/deploy/route';

describe('deploy proxy route', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('requires an authorization token for GET requests', async () => {
    const response = await GET(new Request('http://localhost/api/deploy'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ error: 'Vercel token required' });
  });

  it('returns an error for an unknown GET action', async () => {
    const response = await GET(
      new Request('http://localhost/api/deploy?action=unknown', {
        headers: { Authorization: 'Bearer valid-token-12345' },
      })
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ error: 'Unknown action' });
  });

  it('lists projects for the projects action', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ projects: [{ id: 'p1', name: 'demo' }] }),
    } as Response);

    const response = await GET(
      new Request('http://localhost/api/deploy?action=projects', {
        headers: { Authorization: 'Bearer valid-token-12345' },
      })
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ projects: [{ id: 'p1', name: 'demo' }] });
  });

  it('creates a sanitized vercel project slug', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'project-id', name: 'my-app' }),
    } as Response);

    const response = await POST(
      new Request('http://localhost/api/deploy', {
        method: 'POST',
        headers: {
          Authorization: 'Bearer valid-token-12345',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ projectName: 'My App!!!' }),
      })
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({
      success: true,
      projectName: 'my-app',
      projectUrl: 'https://my-app.vercel.app',
    });
  });
});