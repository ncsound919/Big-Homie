import { NextRequest, NextResponse } from 'next/server';

/* ══════════════════════════════════════════════════
   /api/proxy — Lightweight HTML proxy for iframe
   browsing.  Fetches the target URL server-side and
   strips X-Frame-Options / frame-ancestors so the
   response can be rendered inside an <iframe>.
   ══════════════════════════════════════════════════ */

const MAX_BODY = 10 * 1024 * 1024; // 10 MB cap
const FETCH_TIMEOUT = 15_000; // 15 s
const BLOCKED_PORTS = new Set([
  '21', '22', '23', '25', '53', '111', '135', '137', '138', '139', '143',
  '389', '445', '465', '587', '636', '993', '995', '1433', '1521', '2049',
  '2375', '2376', '3306', '3389', '5432', '5900', '6379', '9200', '11211', '27017',
]);

function isLocalHostname(hostname: string): boolean {
  return hostname === 'localhost' || hostname.endsWith('.localhost');
}

function isBlockedIpv4(hostname: string): boolean {
  if (!/^\d{1,3}(?:\.\d{1,3}){3}$/.test(hostname)) {
    return false;
  }

  const parts = hostname.split('.').map((part) => Number(part));
  if (parts.some((part) => Number.isNaN(part) || part < 0 || part > 255)) {
    return true;
  }

  const [a, b] = parts;
  return (
    a === 0 ||
    a === 10 ||
    a === 127 ||
    (a === 169 && b === 254) ||
    (a === 172 && b >= 16 && b <= 31) ||
    (a === 192 && b === 168)
  );
}

function isBlockedIpv6(hostname: string): boolean {
  const normalized = hostname.toLowerCase();

  return (
    normalized === '::1' ||
    normalized.startsWith('fe8:') ||
    normalized.startsWith('fe9:') ||
    normalized.startsWith('fea:') ||
    normalized.startsWith('feb:') ||
    normalized.startsWith('fc') ||
    normalized.startsWith('fd')
  );
}

/** Reject URLs that point at private / internal IPs (SSRF guard). */
function isBlockedHost(urlStr: string): boolean {
  try {
    const { hostname, password, port, username } = new URL(urlStr);
    const normalized = hostname.toLowerCase();

    return (
      !normalized ||
      Boolean(username) ||
      Boolean(password) ||
      (Boolean(port) && BLOCKED_PORTS.has(port)) ||
      isLocalHostname(normalized) ||
      isBlockedIpv4(normalized) ||
      isBlockedIpv6(normalized)
    );
  } catch {
    return true;
  }
}

function createProxyHeaders(contentType: string, isHtml: boolean): HeadersInit {
  return {
    'Content-Type': contentType,
    'Cache-Control': isHtml ? 'private, no-store' : 'private, max-age=300',
    'Referrer-Policy': 'no-referrer',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
    ...(isHtml
      ? {
          'Content-Security-Policy':
            "default-src * data: blob: 'unsafe-inline' 'unsafe-eval'; frame-ancestors 'self'; sandbox allow-forms allow-popups allow-scripts allow-same-origin",
        }
      : {}),
  };
}

export async function GET(req: NextRequest) {
  const target = req.nextUrl.searchParams.get('url');
  if (!target) {
    return NextResponse.json({ error: 'Missing ?url= parameter' }, { status: 400 });
  }

  // Only allow http(s) schemes
  if (!/^https?:\/\//i.test(target)) {
    return NextResponse.json({ error: 'Only http/https URLs are allowed' }, { status: 400 });
  }

  if (isBlockedHost(target)) {
    return NextResponse.json({ error: 'Blocked host' }, { status: 403 });
  }

  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT);

    const upstream = await fetch(target, {
      signal: controller.signal,
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
      },
      redirect: 'follow',
    });
    clearTimeout(timer);

    const ct = upstream.headers.get('content-type') ?? 'text/html';

    // For non-HTML content, just stream it through
    if (!ct.includes('text/html') && !ct.includes('application/xhtml')) {
      const body = await upstream.arrayBuffer();
      if (body.byteLength > MAX_BODY) {
        return NextResponse.json({ error: 'Response too large' }, { status: 413 });
      }
      return new NextResponse(body, {
        status: upstream.status,
        headers: createProxyHeaders(ct, false),
      });
    }

    let html = await upstream.text();
    if (html.length > MAX_BODY) {
      return NextResponse.json({ error: 'Response too large' }, { status: 413 });
    }

    // Inject <base> so relative URLs resolve against the original domain
    const origin = new URL(target);
    const baseHref = `${origin.protocol}//${origin.host}`;
    if (!/<base\b/i.test(html)) {
      html = html.replace(
        /(<head[^>]*>)/i,
        `$1<base href="${baseHref}/" />`,
      );
    }

    return new NextResponse(html, {
      status: upstream.status,
      headers: createProxyHeaders(ct, true),
    });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : 'Failed to fetch';
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
