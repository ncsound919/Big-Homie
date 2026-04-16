// Vercel deployment proxy route.
// The Vercel token comes from the client as a Bearer token — never stored server-side.

import { NextResponse } from 'next/server';

function vHeaders(token: string) {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

function extractToken(request: Request): string | null {
  const auth = request.headers.get('Authorization');
  if (!auth?.startsWith('Bearer ')) return null;
  const t = auth.slice(7).trim();
  if (t.length < 10) return null;
  return t;
}

// List Vercel projects or get deployment status
export async function GET(request: Request) {
  const token = extractToken(request);
  if (!token) return NextResponse.json({ error: 'Vercel token required' }, { status: 401 });

  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action') ?? 'projects';

  if (action === 'projects') {
    const res = await fetch('https://api.vercel.com/v9/projects?limit=20', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      return NextResponse.json({ error: 'Failed to list projects', status: res.status }, { status: res.status });
    }
    const data = await res.json() as { projects: unknown[] };
    return NextResponse.json({ projects: data.projects ?? [] });
  }

  if (action === 'deployments') {
    const projectId = searchParams.get('projectId');
    if (!projectId || !/^[\w-]+$/.test(projectId)) return NextResponse.json({ error: 'valid projectId required' }, { status: 400 });
    const res = await fetch(`https://api.vercel.com/v6/deployments?projectId=${encodeURIComponent(projectId)}&limit=5`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return NextResponse.json({ error: 'Failed to fetch deployments' }, { status: res.status });
    return NextResponse.json(await res.json());
  }

  return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
}

// Create Vercel project and optionally trigger a deployment
export async function POST(request: Request) {
  const token = extractToken(request);
  if (!token) return NextResponse.json({ error: 'Vercel token required' }, { status: 401 });

  const body = await request.json() as {
    projectName?: string;
    gitRepo?: string;   // "owner/repo" format
    framework?: string;
    envVars?: Array<{ key: string; value: string }>;
    rootDirectory?: string;
  };

  const { projectName, gitRepo, framework, envVars, rootDirectory } = body;
  if (!projectName) {
    return NextResponse.json({ error: 'projectName required' }, { status: 400 });
  }

  const slug = projectName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 52);
  if (!slug) {
    return NextResponse.json({ error: 'Project name produces an empty slug' }, { status: 400 });
  }
  const payload: Record<string, unknown> = {
    name: slug,
    framework: framework ?? 'nextjs',
  };

  if (gitRepo) {
    payload.gitRepository = { type: 'github', repo: gitRepo };
  }

  if (rootDirectory) {
    payload.rootDirectory = rootDirectory;
  }

  if (envVars?.length) {
    payload.environmentVariables = envVars.map(e => ({
      key: e.key,
      value: e.value,
      type: 'plain',
      target: ['production', 'preview', 'development'],
    }));
  }

  const res = await fetch('https://api.vercel.com/v9/projects', {
    method: 'POST',
    headers: vHeaders(token),
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return NextResponse.json({ error: 'Vercel project creation failed', details: err }, { status: res.status });
  }

  const project = await res.json() as { id: string; name: string };
  return NextResponse.json({
    success: true,
    projectId: project.id,
    projectName: project.name,
    projectUrl: `https://${project.name}.vercel.app`,
    dashboardUrl: `https://vercel.com/${project.name}`,
    gitConnected: !!gitRepo,
  });
}
