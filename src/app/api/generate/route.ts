import { NextResponse } from 'next/server';
import { generateSite, type GeneratorInput } from '@/lib/generate-site';

function normalizeText(value: unknown, maxLength: number): string {
  return typeof value === 'string'
    ? value.replace(/\s+/g, ' ').trim().slice(0, maxLength)
    : '';
}

export async function POST(request: Request) {
  let body: GeneratorInput;
  try {
    body = (await request.json()) as GeneratorInput;
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const input: GeneratorInput = {
    name: normalizeText(body.name, 80),
    description: normalizeText(body.description, 2000),
    type: normalizeText(body.type, 80),
    audience: normalizeText(body.audience, 120),
  };

  if (!input.name || !input.description) {
    return NextResponse.json({ error: 'name and description are required' }, { status: 400 });
  }

  const site = generateSite(input);
  return NextResponse.json(site);
}
