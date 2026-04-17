import { NextResponse } from 'next/server';
import { Prisma } from '@prisma/client';
import { db } from '@/lib/db';

function getAgentApiKey(): string {
  return process.env.BIG_HOMIE_AGENT_API_KEY || process.env.AGENT_API_KEY || '';
}

function getBearerToken(request: Request): string | null {
  const auth = request.headers.get('authorization');
  if (!auth?.startsWith('Bearer ')) {
    return null;
  }

  return auth.slice('Bearer '.length).trim() || null;
}

function isLoopbackHostname(hostname: string): boolean {
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1';
}

function hasTrustedLocalOrigin(request: Request): boolean {
  const requestUrl = new URL(request.url);
  if (!isLoopbackHostname(requestUrl.hostname)) {
    return false;
  }

  const source = request.headers.get('origin') ?? request.headers.get('referer');
  if (!source) {
    return false;
  }

  try {
    const sourceUrl = new URL(source);
    return isLoopbackHostname(sourceUrl.hostname);
  } catch {
    return false;
  }
}

function isAuthorized(request: Request, options?: { requireApiKey?: boolean }): boolean {
  const requireApiKey = options?.requireApiKey ?? false;
  const bearerToken = getBearerToken(request);
  const agentApiKey = getAgentApiKey();

  if (agentApiKey && bearerToken === agentApiKey) {
    return true;
  }

  if (requireApiKey) {
    return false;
  }

  return hasTrustedLocalOrigin(request);
}

function unauthorizedResponse() {
  return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
}

const VALID_AGENT_TYPES = new Set(['config', 'code', 'folder']);

function serializeAgent(
  agent: Awaited<ReturnType<typeof db.agent.findMany>>[number],
  includeSensitive: boolean,
) {
  return {
    id: agent.id,
    name: agent.name,
    description: agent.description,
    type: agent.type,
    securityTier: agent.securityTier,
    enabled: agent.enabled,
    addedAt: agent.addedAt.toISOString(),
    ...(includeSensitive ? { config: agent.config, code: agent.code } : {}),
    ...(includeSensitive && agent.type === 'folder' ? { files: agent.config } : {}),
  };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const includeSensitive = searchParams.get('includeSensitive') === '1';

  if (!isAuthorized(request, { requireApiKey: includeSensitive })) {
    return unauthorizedResponse();
  }

  const agents = await db.agent.findMany({ orderBy: { addedAt: 'desc' } });
  return NextResponse.json(agents.map((agent) => serializeAgent(agent, includeSensitive)));
}

export async function POST(request: Request) {
  if (!isAuthorized(request)) {
    return unauthorizedResponse();
  }

  const body = await request.json();

  if (!VALID_AGENT_TYPES.has(body.type)) {
    return NextResponse.json({ error: 'Invalid type' }, { status: 400 });
  }

  if (body.id !== undefined && body.id !== null && typeof body.id !== 'string') {
    return NextResponse.json({ error: 'Invalid id' }, { status: 400 });
  }

  let configData: Prisma.InputJsonValue | typeof Prisma.JsonNull = Prisma.JsonNull;
  if (body.type === 'config') {
    configData = body.config;
  } else if (body.type === 'folder') {
    configData = body.files ?? Prisma.JsonNull;
  }

  const updateData = {
    name: body.name,
    description: body.description,
    type: body.type,
    config: configData,
    code: body.type === 'code' ? body.code : null,
    securityTier: body.securityTier,
    enabled: body.enabled,
  };

  const createData = {
    name: body.name,
    description: body.description,
    type: body.type,
    config: configData,
    code: body.type === 'code' ? body.code : null,
    securityTier: body.securityTier || 'full',
    enabled: body.enabled ?? true,
    addedAt: new Date(),
  };

  const agent = body.id
    ? await db.agent.update({
        where: { id: body.id },
        data: updateData,
      })
    : await db.agent.create({
        data: createData,
      });
  return NextResponse.json(agent);
}

export async function PUT(request: Request) {
  if (!isAuthorized(request)) {
    return unauthorizedResponse();
  }

  const body = await request.json();
  const { id, ...data } = body;
  if (!id || typeof id !== 'string') {
    return NextResponse.json({ error: 'Missing id' }, { status: 400 });
  }

  const agent = await db.agent.update({
    where: { id },
    data: { ...data, updatedAt: new Date() },
  });
  return NextResponse.json(agent);
}

export async function DELETE(request: Request) {
  if (!isAuthorized(request)) {
    return unauthorizedResponse();
  }

  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');
  if (!id) {
    return NextResponse.json({ error: 'Missing id' }, { status: 400 });
  }
  await db.agent.delete({ where: { id } });
  return NextResponse.json({ success: true });
}
