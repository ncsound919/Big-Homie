import { describe, expect, it } from 'vitest';
import { POST } from '@/app/api/generate/route';

describe('generate route', () => {
  it('rejects missing required fields', async () => {
    const response = await POST(new Request('http://localhost/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: '', description: '' }),
    }));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ error: 'name and description are required' });
  });

  it('normalizes whitespace before generating HTML', async () => {
    const response = await POST(new Request('http://localhost/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: '  Happy   Paws  ',
        description: '  Dog   grooming   website   for   city   pet owners.  ',
        type: '  Business   Website ',
        audience: '  Pet   owners ',
      }),
    }));

    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.title).toContain('Happy Paws');
    expect(body.html).toContain('Happy Paws');
    expect(body.html).not.toContain('Happy   Paws');
  });
});