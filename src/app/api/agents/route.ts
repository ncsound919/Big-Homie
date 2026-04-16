import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET() {
  const agents = await db.agent.findMany({ orderBy: { addedAt: 'desc' } });
  return NextResponse.json(agents.map(a => ({
    id: a.id,
    name: a.name,
    description: a.description,
    type: a.type,
    config: a.config,
    code: a.code,
    securityTier: a.securityTier,
    enabled: a.enabled,
    addedAt: a.addedAt.toISOString(),
  })));
}

export async function POST(request: Request) {
  const body = await request.json();

  if (body.type !== 'config' && body.type !== 'code') {
    return NextResponse.json({ error: 'Invalid type' }, { status: 400 });
  }

  if (body.id !== undefined && body.id !== null && typeof body.id !== 'string') {
    return NextResponse.json({ error: 'Invalid id' }, { status: 400 });
  }

  const updateData = {
    name: body.name,
    description: body.description,
    type: body.type,
    config: body.type === 'config' ? body.config : null,
    code: body.type === 'code' ? body.code : null,
    securityTier: body.securityTier,
    enabled: body.enabled,
  };

  const createData = {
    name: body.name,
    description: body.description,
    type: body.type,
    config: body.type === 'config' ? body.config : null,
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
  const body = await request.json();
  const { id, ...data } = body;
  const agent = await db.agent.update({
    where: { id },
    data: { ...data, updatedAt: new Date() },
  });
  return NextResponse.json(agent);
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');
  if (!id) {
    return NextResponse.json({ error: 'Missing id' }, { status: 400 });
  }
  await db.agent.delete({ where: { id } });
  return NextResponse.json({ success: true });
}