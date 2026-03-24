import { NextRequest } from 'next/server';

export const maxDuration = 30;

/**
 * POST /api/memory
 * Receives a conversation history and asks the AI to extract a short user profile.
 * Returns a concise summary string that will be stored in the client's localStorage.
 */
export async function POST(req: NextRequest) {
  const { messages } = await req.json();

  if (!messages || messages.length < 2) {
    return new Response(JSON.stringify({ profile: null }), {
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const baseUrl = process.env.AI_BASE_URL || 'http://113.160.201.164:8003/v1';
  const apiKey = process.env.AI_API_KEY;
  const model = process.env.AI_MODEL || 'local-fast';

  if (!apiKey) {
    return new Response(JSON.stringify({ profile: null }), { status: 200 });
  }

  // Condense conversation to a short text block for the AI to analyze
  const conversationText = messages
    .filter((m: { role: string }) => m.role !== 'error')
    .map((m: { role: string; content: string }) => `${m.role === 'user' ? 'Khách' : 'AI'}: ${m.content}`)
    .join('\n');

  const extractionPrompt = `Đây là đoạn hội thoại giữa khách hàng và nhân viên AI:\n\n${conversationText}\n\n---\nDựa vào đoạn hội thoại trên, hãy tóm tắt trong 1-2 câu ngắn gọn những gì bạn biết về khách hàng (tên, nhu cầu dịch vụ, phong cách giao tiếp, vấn đề đã đề cập). Nếu không có thông tin gì hữu ích, hãy trả lời đúng một chữ: EMPTY.`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 25000);

  try {
    const aiResponse = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        messages: [
          { role: 'user', content: extractionPrompt },
        ],
        max_tokens: 200,
        stream: false,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!aiResponse.ok) {
      return new Response(JSON.stringify({ profile: null }), { status: 200 });
    }

    const data = await aiResponse.json();
    const rawProfile = data?.choices?.[0]?.message?.content?.trim() ?? null;

    // Strip any thinking tags the model might output
    let profile = rawProfile;
    if (profile) {
      if (profile.toLowerCase().includes('</think>')) {
        profile = profile.split(/<\/think>/i).pop()?.trim() ?? null;
      }
      if (profile?.toLowerCase().includes('</thinking>')) {
        profile = profile.split(/<\/thinking>/i).pop()?.trim() ?? null;
      }
      // Discard if the model said EMPTY or the extraction is too short
      if (!profile || profile.toUpperCase() === 'EMPTY' || profile.length < 5) {
        profile = null;
      }
    }

    return new Response(JSON.stringify({ profile }), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    clearTimeout(timeoutId);
    return new Response(JSON.stringify({ profile: null }), { status: 200 });
  }
}
