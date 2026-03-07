import { NextRequest, NextResponse } from 'next/server';

const configuredBackend = (process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || '').trim();
const backendBase = configuredBackend.endsWith('/') ? configuredBackend.slice(0, -1) : configuredBackend;

export const dynamic = 'force-dynamic';

function shouldIncludeBody(method: string): boolean {
  return !['GET', 'HEAD'].includes(method.toUpperCase());
}

function getBackendRoot(base: string): string {
  return base.replace(/\/api\/v1$/, '');
}

function buildTargetUrl(req: NextRequest, path: string[]): string {
  const joinedPath = path.join('/');

  // Convenience health pass-through even when BACKEND_API_URL includes /api/v1.
  if (joinedPath === 'health') {
    return `${getBackendRoot(backendBase)}/health${req.nextUrl.search}`;
  }

  return `${backendBase}/${joinedPath}${req.nextUrl.search}`;
}

async function proxy(req: NextRequest, path: string[]): Promise<NextResponse> {
  if (!backendBase) {
    return NextResponse.json(
      { detail: 'Missing BACKEND_API_URL or NEXT_PUBLIC_API_URL on Vercel.' },
      { status: 500 },
    );
  }

  const headers = new Headers(req.headers);
  headers.delete('host');
  headers.delete('connection');
  headers.delete('content-length');

  const targetUrl = buildTargetUrl(req, path);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 25000);

  try {
    const upstream = await fetch(targetUrl, {
      method: req.method,
      headers,
      body: shouldIncludeBody(req.method) ? await req.arrayBuffer() : undefined,
      redirect: 'manual',
      cache: 'no-store',
      signal: controller.signal,
    });

    const responseHeaders = new Headers(upstream.headers);
    responseHeaders.delete('content-encoding');

    return new NextResponse(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      return NextResponse.json(
        { detail: 'Backend request timed out (25s). Wake Render and retry.' },
        { status: 504 },
      );
    }

    return NextResponse.json(
      { detail: 'Cannot reach backend service from Vercel function.' },
      { status: 502 },
    );
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