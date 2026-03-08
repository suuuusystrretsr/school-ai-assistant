import { NextRequest, NextResponse } from 'next/server';

function sanitizeUrl(raw: string | undefined): string {
  if (!raw) return '';
  return raw.trim().replace(/^['\"]+|['\"]+$/g, '');
}

const configuredBackend = sanitizeUrl(process.env.BACKEND_API_URL) || sanitizeUrl(process.env.NEXT_PUBLIC_API_URL);
const backendBase = configuredBackend.endsWith('/') ? configuredBackend.slice(0, -1) : configuredBackend;

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

function shouldIncludeBody(method: string): boolean {
  return !['GET', 'HEAD'].includes(method.toUpperCase());
}

function getBackendRoot(base: string): string {
  return base.replace(/\/api\/v1$/, '');
}

function buildTargetUrl(req: NextRequest, path: string[]): string {
  const joinedPath = path.join('/');
  if (joinedPath === 'health') {
    return `${getBackendRoot(backendBase)}/health${req.nextUrl.search}`;
  }
  return `${backendBase}/${joinedPath}${req.nextUrl.search}`;
}

function getTimeoutMs(path: string): number {
  if (path === 'exams/generate') return 70000;
  if (/^exams\/\d+\/submit$/.test(path)) return 30000;
  return 20000;
}
async function proxy(req: NextRequest, path: string[]): Promise<NextResponse> {
  if (!backendBase) {
    return NextResponse.json({ detail: 'Missing BACKEND_API_URL or NEXT_PUBLIC_API_URL on Vercel.' }, { status: 500 });
  }

  const host = req.headers.get('host') || '';
  if (host && backendBase.includes(host)) {
    return NextResponse.json(
      { detail: 'BACKEND_API_URL points to this Vercel app. Set it to Render API URL.' },
      { status: 500 },
    );
  }

  const headers = new Headers(req.headers);
  headers.delete('host');
  headers.delete('connection');
  headers.delete('content-length');
  headers.delete('accept-encoding');

  const joinedPath = path.join('/');
  const targetUrl = buildTargetUrl(req, path);
  const controller = new AbortController();
  const timeoutMs = getTimeoutMs(joinedPath);
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const upstream = await fetch(targetUrl, {
      method: req.method,
      headers,
      body: shouldIncludeBody(req.method) ? await req.arrayBuffer() : undefined,
      redirect: 'follow',
      cache: 'no-store',
      signal: controller.signal,
    });

    const bodyText = await upstream.text();
    const contentType = upstream.headers.get('content-type') || 'application/json; charset=utf-8';

    return new NextResponse(bodyText, {
      status: upstream.status,
      headers: {
        'content-type': contentType,
        'cache-control': 'no-store',
      },
    });
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      return NextResponse.json({ detail: `Backend request timed out (${timeoutMs}ms). Wake Render and retry.` }, { status: 504 });
    }
    return NextResponse.json({ detail: 'Cannot reach backend service from Vercel function.' }, { status: 502 });
  } finally {
    clearTimeout(timeout);
  }
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function POST(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function PUT(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function PATCH(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function DELETE(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
