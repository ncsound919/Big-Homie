/**
 * API route tests for /api/upgrade-sweep
 *
 * Uses vi.spyOn on the already-imported fs.promises binding so we avoid
 * vi.mock hoisting issues entirely. The in-memory fileData store is shared
 * between test helpers and the mock implementations.
 */
import { promises as fsPromises } from 'fs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// ── In-memory file store ─────────────────────────────────────────────
const fileData: Record<string, string> = {};

vi.spyOn(fsPromises, 'readFile').mockImplementation(async (p: any) => {
  const name = String(p).replace(/\\/g, '/').split('/').pop()!;
  if (name in fileData) return fileData[name];
  throw Object.assign(new Error('ENOENT'), { code: 'ENOENT' });
});
vi.spyOn(fsPromises, 'writeFile').mockImplementation(async (p: any, d: any) => {
  const name = String(p).replace(/\\/g, '/').split('/').pop()!;
  fileData[name] = String(d);
});
vi.spyOn(fsPromises, 'rename').mockImplementation(async (o: any, n: any) => {
  const on = String(o).replace(/\\/g, '/').split('/').pop()!;
  const nn = String(n).replace(/\\/g, '/').split('/').pop()!;
  if (on in fileData) { fileData[nn] = fileData[on]; delete fileData[on]; }
});
vi.spyOn(fsPromises, 'open').mockImplementation(async () => ({ close: vi.fn() }) as any);
(fsPromises as any).unlink = vi.fn(async () => {});

// Now import the route handlers — they will get our spied fs
const { GET, POST } = await import('@/app/api/upgrade-sweep/route');

// ── Helpers ──────────────────────────────────────────────────────────

function req(body: unknown): Request {
  return new Request('http://localhost/api/upgrade-sweep', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

function seed(requests: any[]) {
  fileData['upgrade-launch-queue.json'] = JSON.stringify({ requests });
}

function stored(): any[] {
  const raw = fileData['upgrade-launch-queue.json'];
  return raw ? (JSON.parse(raw).requests ?? []) : [];
}

beforeEach(() => {
  for (const k of Object.keys(fileData)) delete fileData[k];
});

// ── GET ──────────────────────────────────────────────────────────────

describe('GET /api/upgrade-sweep', () => {
  it('returns targets and empty queue on fresh start', async () => {
    const res = await GET();
    const data = await res.json();
    expect(res.status).toBe(200);
    expect(data.targets.length).toBeGreaterThanOrEqual(2);
    expect(data.queue).toEqual([]);
    expect(data.history).toEqual([]);
  });

  it('separates active vs history', async () => {
    seed([
      { requestId: 'a', targetId: 'x', status: 'queued', createdAt: '2026-01-01' },
      { requestId: 'b', targetId: 'y', status: 'completed', createdAt: '2026-01-01', report: { finishedAt: '2026-01-02' } },
      { requestId: 'c', targetId: 'z', status: 'failed', createdAt: '2026-01-01' },
    ]);
    const data = await (await GET()).json();
    expect(data.queue).toHaveLength(1);
    expect(data.history).toHaveLength(2);
  });

  it('every target has an approval plan', async () => {
    const data = await (await GET()).json();
    for (const t of data.targets) {
      expect(['auto', 'review', 'manual']).toContain(t.approval.tier);
    }
  });
});

// ── POST launch ──────────────────────────────────────────────────────

describe('POST launch', () => {
  it('rejects missing action', async () => {
    expect((await POST(req({}))).status).toBe(400);
  });

  it('rejects invalid action', async () => {
    expect((await POST(req({ action: 'destroy' }))).status).toBe(400);
  });

  it('rejects malformed JSON', async () => {
    const r = new Request('http://localhost', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{bad',
    });
    const res = await POST(r);
    expect(res.status).toBe(400);
    expect((await res.json()).error).toContain('Invalid JSON');
  });

  it('rejects missing targetId', async () => {
    expect((await POST(req({ action: 'launch' }))).status).toBe(400);
  });

  it('rejects unknown targetId', async () => {
    expect((await POST(req({ action: 'launch', targetId: 'bogus' }))).status).toBe(404);
  });

  it('creates queue entry for valid target', async () => {
    const data = await (await POST(req({ action: 'launch', targetId: 'agentbrowser' }))).json();
    expect(data.deduped).toBe(false);
    expect(data.request.targetId).toBe('agentbrowser');
    expect(data.request.requestId).toMatch(/^upgrade-/);
  });

  it('deduplicates active requests', async () => {
    await POST(req({ action: 'launch', targetId: 'agentbrowser' }));
    const data = await (await POST(req({ action: 'launch', targetId: 'agentbrowser' }))).json();
    expect(data.deduped).toBe(true);
  });

  it('allows re-launch after completion', async () => {
    await POST(req({ action: 'launch', targetId: 'research-content' }));
    const q = stored();
    q[0].status = 'completed';
    seed(q);
    const data = await (await POST(req({ action: 'launch', targetId: 'research-content' }))).json();
    expect(data.deduped).toBe(false);
  });
});

// ── POST approve ─────────────────────────────────────────────────────

describe('POST approve', () => {
  it('rejects missing requestId', async () => {
    expect((await POST(req({ action: 'approve' }))).status).toBe(400);
  });

  it('rejects unknown requestId', async () => {
    seed([]);
    expect((await POST(req({ action: 'approve', requestId: 'x' }))).status).toBe(404);
  });

  it('rejects approve on non-awaiting_approval status', async () => {
    seed([{ requestId: 'r1', targetId: 'agentbrowser', status: 'queued' }]);
    expect((await POST(req({ action: 'approve', requestId: 'r1' }))).status).toBe(409);
  });

  it('approves awaiting_approval request', async () => {
    seed([{ requestId: 'r2', targetId: 'agentbrowser', status: 'awaiting_approval', autoExecute: false, approvalRequired: true }]);
    const data = await (await POST(req({ action: 'approve', requestId: 'r2' }))).json();
    expect(data.request.status).toBe('queued');
    expect(data.request.autoExecute).toBe(true);
  });
});

// ── Queue rotation ───────────────────────────────────────────────────

describe('Queue rotation', () => {
  it('trims terminal entries to MAX_QUEUE_HISTORY', async () => {
    seed(Array.from({ length: 250 }, (_, i) => ({
      requestId: `old-${i}`, targetId: 'agentbrowser', status: 'completed', createdAt: '2025-01-01',
    })));
    await POST(req({ action: 'launch', targetId: 'research-content' }));
    const q = stored();
    const terminal = q.filter((r: any) => ['completed', 'failed'].includes(r.status));
    expect(terminal.length).toBeLessThanOrEqual(200);
  });
});
