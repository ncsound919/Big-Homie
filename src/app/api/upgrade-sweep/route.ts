import { promises as fs } from 'fs';
import path from 'path';
import { NextResponse } from 'next/server';

import {
  MASSIVE_UPGRADE_SWEEP,
  determineApprovalPlan,
  buildUpgradeRequestMessage,
  type UpgradeLaunchRequest,
} from '@/lib/upgrade-sweep';

const WORKSPACE_ROOT = path.resolve(process.cwd(), '..');
const UPGRADE_QUEUE_PATH = path.join(WORKSPACE_ROOT, 'upgrade-launch-queue.json');
const LOCK_PATH = UPGRADE_QUEUE_PATH + '.lock';
const MAX_QUEUE_HISTORY = 200;

interface QueueFileShape {
  requests: UpgradeLaunchRequest[];
}

async function acquireLock(timeout = 5000): Promise<void> {
  const deadline = Date.now() + timeout;
  while (true) {
    try {
      const fd = await fs.open(LOCK_PATH, 'wx');
      await fd.close();
      return;
    } catch {
      if (Date.now() > deadline) {
        // Stale lock — break it
        try { await fs.unlink(LOCK_PATH); } catch { /* ignore */ }
        continue;
      }
      await new Promise(r => setTimeout(r, 50));
    }
  }
}

async function releaseLock(): Promise<void> {
  try { await fs.unlink(LOCK_PATH); } catch { /* ignore */ }
}

async function readQueue(): Promise<QueueFileShape> {
  try {
    const raw = await fs.readFile(UPGRADE_QUEUE_PATH, 'utf8');
    const parsed = JSON.parse(raw) as Partial<QueueFileShape>;
    if (!parsed || !Array.isArray(parsed.requests)) return { requests: [] };
    return { requests: parsed.requests };
  } catch {
    return { requests: [] };
  }
}

async function writeQueue(queue: QueueFileShape): Promise<void> {
  // Trim terminal items to keep file bounded
  const active = queue.requests.filter(r => !['completed', 'failed'].includes(r.status));
  const terminal = queue.requests.filter(r => ['completed', 'failed'].includes(r.status));
  const trimmed = { requests: [...active, ...terminal.slice(0, MAX_QUEUE_HISTORY)] };
  const tmp = UPGRADE_QUEUE_PATH + '.tmp';
  await fs.writeFile(tmp, JSON.stringify(trimmed, null, 2), 'utf8');
  await fs.rename(tmp, UPGRADE_QUEUE_PATH);
}

function buildQueueRequest(targetId: string): UpgradeLaunchRequest | null {
  const target = MASSIVE_UPGRADE_SWEEP.find(item => item.targetId === targetId);
  if (!target) return null;

  const approval = determineApprovalPlan(target);
  const requestId = `upgrade-${Date.now()}-${target.targetId}`;

  return {
    requestId,
    createdAt: new Date().toISOString(),
    requestedBy: 'AgentBrowser',
    targetId: target.targetId,
    targetName: target.targetName,
    summary: target.summary,
    requestMessage: buildUpgradeRequestMessage(target),
    approvalTier: approval.tier,
    approvalRequired: approval.approvalRequired,
    autoExecute: approval.autoExecute,
    approvalRationale: approval.rationale,
    status: approval.autoExecute ? 'queued' : 'awaiting_approval',
    recommendedRepos: target.recommendedRepos,
  };
}

export async function GET() {
  await acquireLock();
  try {
    const queue = await readQueue();
    const queueByTarget = new Map(
      queue.requests
        .filter(r => !['completed', 'failed'].includes(r.status))
        .map(request => [request.targetId, request]),
    );

    const history = queue.requests
      .filter(r => r.status === 'completed' || r.status === 'failed')
      .sort((a, b) => (b.report?.finishedAt ?? b.createdAt).localeCompare(a.report?.finishedAt ?? a.createdAt))
      .slice(0, 50);

    return NextResponse.json({
      targets: MASSIVE_UPGRADE_SWEEP.map(target => ({
        ...target,
        approval: determineApprovalPlan(target),
        activeRequest: queueByTarget.get(target.targetId) ?? null,
      })),
      queue: queue.requests.filter(r => !['completed', 'failed'].includes(r.status)),
      history,
    });
  } finally {
    await releaseLock();
  }
}

const VALID_ACTIONS = new Set(['launch', 'approve']);
const MAX_BODY_LENGTH = 4096;

export async function POST(request: Request) {
  // Guard against oversized bodies
  const contentLength = request.headers.get('content-length');
  if (contentLength && parseInt(contentLength, 10) > MAX_BODY_LENGTH) {
    return NextResponse.json({ error: 'Request body too large' }, { status: 413 });
  }

  let body: { action?: string; targetId?: string; requestId?: string };
  try {
    body = await request.json() as typeof body;
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  if (!body || typeof body !== 'object' || !body.action || !VALID_ACTIONS.has(body.action)) {
    return NextResponse.json({ error: 'action must be "launch" or "approve"' }, { status: 400 });
  }

  await acquireLock();
  try {
    const queue = await readQueue();

    if (body.action === 'launch') {
      if (!body.targetId || typeof body.targetId !== 'string') {
        return NextResponse.json({ error: 'targetId is required' }, { status: 400 });
      }

      const existing = queue.requests.find(
        r => r.targetId === body.targetId && ['queued', 'awaiting_approval', 'running'].includes(r.status)
      );
      if (existing) {
        return NextResponse.json({ request: existing, deduped: true });
      }

      const requestItem = buildQueueRequest(body.targetId);
      if (!requestItem) {
        return NextResponse.json({ error: 'Unknown targetId' }, { status: 404 });
      }

      queue.requests.unshift(requestItem);
      await writeQueue(queue);
      return NextResponse.json({ request: requestItem, deduped: false });
    }

    if (body.action === 'approve') {
      if (!body.requestId || typeof body.requestId !== 'string') {
        return NextResponse.json({ error: 'requestId is required' }, { status: 400 });
      }

      const existing = queue.requests.find(r => r.requestId === body.requestId);
      if (!existing) {
        return NextResponse.json({ error: 'Unknown requestId' }, { status: 404 });
      }
      if (existing.status !== 'awaiting_approval') {
        return NextResponse.json({ error: `Cannot approve request in status: ${existing.status}` }, { status: 409 });
      }

      existing.status = 'queued';
      existing.approvalRequired = false;
      existing.autoExecute = true;
      await writeQueue(queue);
      return NextResponse.json({ request: existing });
    }

    return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
  } finally {
    await releaseLock();
  }
}