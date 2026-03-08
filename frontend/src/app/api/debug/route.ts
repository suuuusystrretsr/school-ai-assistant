import { NextResponse } from 'next/server';

function sanitizeUrl(raw: string | undefined): string {
  if (!raw) return '';
  return raw.trim().replace(/^['\"]+|['\"]+$/g, '');
}

export const dynamic = 'force-dynamic';

export async function GET() {
  const nextPublicApiUrl = sanitizeUrl(process.env.NEXT_PUBLIC_API_URL);
  const backendApiUrl = sanitizeUrl(process.env.BACKEND_API_URL);
  const nextPublicWsUrl = sanitizeUrl(process.env.NEXT_PUBLIC_WS_URL);

  const bases = Array.from(new Set(['/api/proxy', nextPublicApiUrl].filter(Boolean)));

  return NextResponse.json({
    ok: true,
    nextPublicApiUrl,
    backendApiUrl,
    nextPublicWsUrl,
    apiBasesTriedByClient: bases,
    proxyConfigured: Boolean(backendApiUrl || nextPublicApiUrl),
  });
}
