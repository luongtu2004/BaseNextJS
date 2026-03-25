import { NextRequest } from 'next/server';
import { AI_CONFIG } from '@/lib/ai-config';
import { stripThinking } from '@/lib/ai-utils';

// Allow up to 60 seconds before Next.js times out this route
export const maxDuration = 60;

export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  const { baseUrl, apiKey, model } = AI_CONFIG;

  if (!apiKey) {
    return new Response(
      JSON.stringify({ error: 'AI API Key is not configured on the server.' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 55000);

  try {
    const aiResponse = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        messages, // Send messages history directly as requested
        max_tokens: 8192,
        stream: true,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!aiResponse.ok || !aiResponse.body) {
      const errorText = await aiResponse.text().catch(() => 'Unknown error');
      return new Response(
        JSON.stringify({ error: `AI Server error: ${aiResponse.status}`, details: errorText }),
        { status: aiResponse.status, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const reader = aiResponse.body.getReader();
    const decoder = new TextDecoder();
    let fullContent = '';
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed === 'data: [DONE]') continue;
        if (trimmed.startsWith('data: ')) {
          try {
            const jsonText = trimmed.slice(6);
            if (jsonText === '[DONE]') continue;
            const json = JSON.parse(jsonText);
            const content = json.choices?.[0]?.delta?.content ?? json.choices?.[0]?.message?.content ?? '';
            // Note: Removed redundant reasoning_content handling to keep it super clean as requested
            if (content) fullContent += content;
          } catch (e) {}
        }
      }
    }

    // Still use stripThinking as a safety measure for any residual tags
    const cleanAnswer = stripThinking(fullContent);

    return new Response(cleanAnswer, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'X-Content-Type-Options': 'nosniff',
        'Cache-Control': 'no-cache, no-store',
      },
    });
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      return new Response(
        JSON.stringify({ error: 'Request timed out. The AI server took too long to respond.' }),
        { status: 504, headers: { 'Content-Type': 'application/json' } }
      );
    }
    return new Response(
      JSON.stringify({ error: 'Internal Server Error', message: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
