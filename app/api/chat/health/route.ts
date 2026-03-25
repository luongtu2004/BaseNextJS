import { NextResponse } from 'next/server';
import { AI_CONFIG } from '@/lib/ai-config';

export const maxDuration = 15;

export async function GET() {
  const { baseUrl, apiKey, model } = AI_CONFIG;

  if (!apiKey) {
    return NextResponse.json({ status: 'error', error: 'API key not configured' }, { status: 500 });
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    // Use the /models endpoint — a lightweight check that doesn't invoke the LLM
    const r = await fetch(`${baseUrl}/models`, {
      headers: { Authorization: `Bearer ${apiKey}` },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (r.ok) {
      const data = await r.json().catch(() => null);
      return NextResponse.json({
        status: 'ok',
        serverUrl: baseUrl,
        model,
        models: data?.data?.map((m: any) => m.id) ?? [],
      });
    }
    return NextResponse.json({ status: 'error', httpStatus: r.status, serverUrl: baseUrl }, { status: 502 });
  } catch (e: any) {
    clearTimeout(timeoutId);
    const isTimeout = e.name === 'AbortError';
    return NextResponse.json(
      { status: 'error', error: isTimeout ? 'Server did not respond within 10s' : e.message, serverUrl: baseUrl },
      { status: isTimeout ? 504 : 502 }
    );
  }
}
