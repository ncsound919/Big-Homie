// GitHub API proxy route.
// The GitHub PAT comes from the client as a Bearer token — never stored server-side.
// All GitHub API calls are proxied through here to avoid CORS and to keep tokens off the client network tab.

import { NextResponse } from 'next/server';

function ghHeaders(token: string) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github.v3+json',
    'User-Agent': 'AgentBrowser/1.0',
  };
}

function extractToken(request: Request): string | null {
  const auth = request.headers.get('Authorization');
  if (!auth?.startsWith('Bearer ')) return null;
  const t = auth.slice(7).trim();
  if (t.length < 10) return null;
  return t;
}

// Validate owner/repo names to prevent SSRF via URL manipulation
const SAFE_SLUG = /^[\w][\w.\-]{0,99}$/;
const SAFE_BRANCH = /^[\w][\w.\-/]{0,249}$/;

function validateSlug(value: string, label: string): string | null {
  if (!value || !SAFE_SLUG.test(value)) return `Invalid ${label}: must be alphanumeric, dots, hyphens, underscores`;
  return null;
}

function validatePath(value: string): string | null {
  if (value.includes('..') || value.startsWith('/')) return 'Invalid path';
  return null;
}

async function proxyGH(url: string, token: string) {
  const res = await fetch(url, { headers: ghHeaders(token) });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    return NextResponse.json(
      { error: 'GitHub API error', status: res.status, details: body },
      { status: res.status }
    );
  }
  return NextResponse.json(await res.json());
}

export async function GET(request: Request) {
  const token = extractToken(request);
  if (!token) return NextResponse.json({ error: 'GitHub token required' }, { status: 401 });

  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action');
  const owner = searchParams.get('owner') ?? '';
  const repo = searchParams.get('repo') ?? '';
  const path = searchParams.get('path') ?? '';
  const ref = searchParams.get('ref') ?? '';

  switch (action) {
    case 'user': {
      return proxyGH('https://api.github.com/user', token);
    }

    case 'repos': {
      // Returns repos the authenticated user has access to
      const url = 'https://api.github.com/user/repos?sort=updated&per_page=50&type=all&affiliation=owner,collaborator,organization_member';
      return proxyGH(url, token);
    }

    case 'tree': {
      const ownerErr = validateSlug(owner, 'owner');
      const repoErr = validateSlug(repo, 'repo');
      if (ownerErr || repoErr) return NextResponse.json({ error: ownerErr ?? repoErr }, { status: 400 });
      const pathErr = validatePath(path);
      if (pathErr) return NextResponse.json({ error: pathErr }, { status: 400 });
      const refPart = ref ? `?ref=${encodeURIComponent(ref)}` : '';
      const url = `https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/contents/${path.split('/').map(encodeURIComponent).join('/')}${refPart}`;
      return proxyGH(url, token);
    }

    case 'file': {
      if (!owner || !repo || !path) return NextResponse.json({ error: 'owner, repo, path required' }, { status: 400 });
      const ownerErr2 = validateSlug(owner, 'owner');
      const repoErr2 = validateSlug(repo, 'repo');
      if (ownerErr2 || repoErr2) return NextResponse.json({ error: ownerErr2 ?? repoErr2 }, { status: 400 });
      const pathErr2 = validatePath(path);
      if (pathErr2) return NextResponse.json({ error: pathErr2 }, { status: 400 });
      const refPart = ref ? `?ref=${encodeURIComponent(ref)}` : '';
      const url = `https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/contents/${path.split('/').map(encodeURIComponent).join('/')}${refPart}`;
      const res = await fetch(url, { headers: ghHeaders(token) });
      if (!res.ok) {
        return NextResponse.json({ error: 'File not found', status: res.status }, { status: res.status });
      }
      const data = await res.json() as {
        content?: string;
        encoding?: string;
        sha: string;
        size: number;
        path: string;
        html_url: string;
      };
      if (data.encoding !== 'base64' || !data.content) {
        return NextResponse.json({ error: 'Unsupported file or encoding' }, { status: 415 });
      }
      // GitHub includes newlines in the base64 — strip them before decoding
      const content = Buffer.from(data.content.replace(/\n/g, ''), 'base64').toString('utf-8');
      return NextResponse.json({
        content,
        sha: data.sha,
        size: data.size,
        path: data.path,
        htmlUrl: data.html_url,
      });
    }

    case 'branches': {
      const ownerErr3 = validateSlug(owner, 'owner');
      const repoErr3 = validateSlug(repo, 'repo');
      if (ownerErr3 || repoErr3) return NextResponse.json({ error: ownerErr3 ?? repoErr3 }, { status: 400 });
      return proxyGH(`https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/branches?per_page=30`, token);
    }

    default:
      return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
  }
}

// Commit a file change to GitHub
export async function PUT(request: Request) {
  const token = extractToken(request);
  if (!token) return NextResponse.json({ error: 'GitHub token required' }, { status: 401 });

  const body = await request.json() as {
    owner?: string;
    repo?: string;
    path?: string;
    content?: string;
    sha?: string;
    message?: string;
    branch?: string;
  };

  const { owner, repo, path, content, sha, message, branch } = body;

  if (!owner || !repo || !path || content === undefined || !sha || !message) {
    return NextResponse.json(
      { error: 'Missing required fields: owner, repo, path, content, sha, message' },
      { status: 400 }
    );
  }

  const ownerErrPut = validateSlug(owner, 'owner');
  const repoErrPut = validateSlug(repo, 'repo');
  if (ownerErrPut || repoErrPut) return NextResponse.json({ error: ownerErrPut ?? repoErrPut }, { status: 400 });
  const pathErrPut = validatePath(path);
  if (pathErrPut) return NextResponse.json({ error: pathErrPut }, { status: 400 });

  const url = `https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/contents/${path.split('/').map(encodeURIComponent).join('/')}`;
  const payload: Record<string, unknown> = {
    message,
    content: Buffer.from(content, 'utf-8').toString('base64'),
    sha,
  };
  if (branch) payload.branch = branch;

  const res = await fetch(url, {
    method: 'PUT',
    headers: { ...ghHeaders(token), 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return NextResponse.json({ error: 'Commit failed', details: err }, { status: res.status });
  }

  const data = await res.json() as {
    commit?: { sha: string; html_url: string };
    content?: { sha: string; html_url: string };
  };

  return NextResponse.json({
    success: true,
    commitSha: data.commit?.sha,
    newFileSha: data.content?.sha,
    commitUrl: data.commit?.html_url,
    fileUrl: data.content?.html_url,
  });
}

// Create a new branch
export async function POST(request: Request) {
  const token = extractToken(request);
  if (!token) return NextResponse.json({ error: 'GitHub token required' }, { status: 401 });

  const body = await request.json() as {
    owner?: string;
    repo?: string;
    newBranch?: string;
    fromBranch?: string;
  };

  const { owner, repo, newBranch, fromBranch } = body;
  if (!owner || !repo || !newBranch) {
    return NextResponse.json({ error: 'owner, repo, newBranch required' }, { status: 400 });
  }

  const ownerErrPost = validateSlug(owner, 'owner');
  const repoErrPost = validateSlug(repo, 'repo');
  if (ownerErrPost || repoErrPost) return NextResponse.json({ error: ownerErrPost ?? repoErrPost }, { status: 400 });
  const sourceBranch = fromBranch ?? 'main';
  if (!SAFE_BRANCH.test(newBranch) || !SAFE_BRANCH.test(sourceBranch)) {
    return NextResponse.json({ error: 'Invalid branch name' }, { status: 400 });
  }

  // Get the SHA of the source branch
  const refRes = await fetch(
    `https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/git/ref/heads/${encodeURIComponent(sourceBranch)}`,
    { headers: ghHeaders(token) }
  );
  if (!refRes.ok) {
    return NextResponse.json({ error: 'Source branch not found' }, { status: 404 });
  }
  const refData = await refRes.json() as { object: { sha: string } };

  // Create the new branch
  const createRes = await fetch(
    `https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/git/refs`,
    {
      method: 'POST',
      headers: { ...ghHeaders(token), 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ref: `refs/heads/${newBranch}`,
        sha: refData.object.sha,
      }),
    }
  );

  if (!createRes.ok) {
    const err = await createRes.json().catch(() => ({}));
    return NextResponse.json({ error: 'Branch creation failed', details: err }, { status: createRes.status });
  }

  return NextResponse.json({ success: true, branch: newBranch });
}
