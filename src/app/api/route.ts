import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const repos = searchParams.get('repos'); // comma-separated "owner/repo" strings

  if (!repos) {
    return NextResponse.json({ error: 'Missing repos parameter' }, { status: 400 });
  }

  const SAFE_REPO = /^[\w.-]+\/[\w.-]+$/;
  const repoList = repos.split(',').slice(0, 10).map(r => r.trim()).filter(r => SAFE_REPO.test(r));
  if (repoList.length === 0) {
    return NextResponse.json({ error: 'No valid repos provided' }, { status: 400 });
  }

  const results = await Promise.allSettled(
    repoList.map(async (repo) => {
      const [owner, name] = repo.split('/');
      const r = await fetch(`https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`, {
        headers: {
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'AgentBrowser/1.0',
        },
        next: { revalidate: 3600 }, // cache for 1 hour
      });
      if (!r.ok) throw new Error(`GitHub API error for ${repo}: ${r.status}`);
      const data = await r.json() as { stargazers_count: number; forks_count: number; open_issues_count: number };
      return { repo: repo.trim(), stars: data.stargazers_count, forks: data.forks_count, issues: data.open_issues_count };
    })
  );

  const stars: Record<string, { stars: number; forks: number; issues: number }> = {};
  for (const result of results) {
    if (result.status === 'fulfilled') {
      stars[result.value.repo] = {
        stars: result.value.stars,
        forks: result.value.forks,
        issues: result.value.issues,
      };
    }
  }

  return NextResponse.json({ stars, fetchedAt: Date.now() });
}
