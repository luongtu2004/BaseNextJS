import { NextRequest } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

// Allow up to 60 seconds before Next.js times out this route
export const maxDuration = 60;

const SYSTEM_PROMPT = `[INST]
BẠN LÀ: Thu Thủy - 🌸 Nhân viên Thu Thủy của "Sàn Dịch Vụ 24/7".
LINH HỒN (SOUL):
- Giúp đỡ tận tâm, không dùng lời sáo rỗng.
- Có quan điểm riêng, không máy móc.
- Trân trọng sự riêng tư và niềm tin của khách hàng.
QUY TẮC:
1. TRẢ LỜI: Ngắn gọn, chuyên nghiệp, tối đa 2-5 câu.
2. XƯNG HÔ: Gọi khách là "Quý khách". Tự xưng là "Em".
3. CẤM: Tuyệt đối không in ra "Thinking Process", không được trả lời sai chính tả. Trả lời ngay kết quả.
4. NGÔN NGỮ: 100% Tiếng Việt.
5. CÁCH TRẢ LỜI: Nếu khách hỏi tên thì trả lời là Thu Thủy. Nếu khách hỏi ngoài lề hoặc nằm ngoài 6 dịch vụ trên, hãy trả lời: "Dạ, em chỉ hỗ trợ 6 nhóm dịch vụ chính của Sàn Dịch Vụ 24/7 thôi ạ. Anh/chị có thể cho em biết nhu cầu của mình thuộc nhóm nào trong số đó không ạ?"
[/INST]`;

/**
 * Rút trích câu trả lời cuối cùng từ "bãi chiến trường" nội dung của Qwen 3.5 7B.
 */
function stripThinking(text: string): string {
  let result = text;

  // 1. ƯU TIÊN: Nếu mô hình dùng thẻ <think>...</think> (như DeepSeek, QwQ)
  // Chúng ta sẽ lấy TOÀN BỘ nội dung nằm sau thẻ đóng </think>
  if (result.toLowerCase().includes('</think>')) {
    const parts = result.split(/<\/think>/i);
    // Lấy phần tử cuối cùng sau thẻ </think> cuối cùng để đảm bảo sạch sẽ
    result = parts[parts.length - 1];
    return result.trim();
  }

  // 2. Nếu không có thẻ <think>, kiểm tra định dạng XML <thinking>...</thinking>
  if (result.toLowerCase().includes('</thinking>')) {
    const parts = result.split(/<\/thinking>/i);
    result = parts[parts.length - 1];
    return result.trim();
  }

  // 3. Dự phòng cho định dạng Qwen 7B (Có chữ "Thinking Process:")
  if (result.toLowerCase().includes('thinking process:')) {
    const splitKeywords = ['*Final Plan:*', '*Revised Draft:*', '*Draft:*', '---', '\n\nChào', '\n\nXin', '\n\nDạ'];
    let bestSplitIndex = -1;
    for (const kw of splitKeywords) {
      const idx = result.lastIndexOf(kw);
      if (idx > bestSplitIndex) {
        bestSplitIndex = kw.startsWith('\n\n') ? idx + 2 : idx + kw.length;
      }
    }

    if (bestSplitIndex !== -1) {
      result = result.substring(bestSplitIndex);
    } else {
      const match = result.match(/\n\n(Chào|Xin|Dạ|Vâng|Em|Mình|Cho hỏi)[^\n]*\n/i);
      if (match && match.index !== undefined) {
        result = result.substring(match.index).trim();
      } else {
        const paragraphs = result.split('\n\n');
        result = paragraphs.slice(-2).join('\n\n');
      }
    }
  }

  return result.replace(/^\*.*?\*\s*$/gm, '').trim();
}

export async function POST(req: NextRequest) {
  const { messages, userProfile } = await req.json();

  // Load knowledge base from the setup directory
  let knowledgeBase = "";
  try {
    const knowledgePath = path.join(process.cwd(), 'setup', 'KNOWLEDGE.md');
    knowledgeBase = await fs.readFile(knowledgePath, 'utf-8');
  } catch (err) {
    console.error("Error loading knowledge base:", err);
  }

  // Build system prompt with knowledge and optional user context injected INSIDE the [INST] tag
  let systemContent = `[INST]
BẠN LÀ: Thu Thủy - 🌸 Nhân viên Thu Thủy của "Sàn Dịch Vụ 24/7".
LINH HỒN (SOUL):
- Giúp đỡ tận tâm, không dùng lời sáo rỗng.
- Có quan điểm riêng, không máy móc.
- Trân trọng sự riêng tư và niềm tin của khách hàng.

BẢN THÂN PHẢI DÙNG KIẾN THỨC DƯỚI ĐÂY ĐỂ TƯ VẤN CHÍNH XÁC:
${knowledgeBase || "Sàn Dịch Vụ 24/7 hỗ trợ 6 nhóm dịch vụ chính."}

${userProfile ? `HỒ SƠ KHÁCH HÀNG: ${userProfile}` : ""}

QUY TẮC:
1. TRẢ LỜI: Ngắn gọn, chuyên nghiệp, tối đa 2-5 câu.
2. XƯNG HÔ: Gọi khách là "Quý khách". Tự xưng là "Em".
3. CẤM: Tuyệt đối không in ra "Thinking Process", không được trả lời sai chính tả. Trả lời ngay kết quả.
4. NGÔN NGỮ: 100% Tiếng Việt.
5. CÁCH TRẢ LỜI: Nếu khách hỏi tên thì trả lời là Thu Thủy. Nếu khách hỏi ngoài lề hoặc nằm ngoài các dịch vụ có trong KIẾN THỨC, hãy trả lời: "Dạ, em chỉ hỗ trợ 6 nhóm dịch vụ chính của Sàn Dịch Vụ 24/7 thôi ạ. Anh/chị có thể cho em biết nhu cầu của mình thuộc nhóm nào trong số đó không ạ?"
[/INST]`;

  const baseUrl = process.env.AI_BASE_URL || 'http://113.160.201.164:8003/v1';
  const apiKey = process.env.AI_API_KEY;
  const model = process.env.AI_MODEL || 'local-main';

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
        messages: [{ role: 'system', content: systemContent }, ...messages],
        max_tokens: 128000, // Tăng lên 128k theo yêu cầu để AI thoải mái "suy nghĩ"
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

    // Strategy: buffer ALL tokens from the AI stream, then strip reasoning before
    // sending the clean final answer to the client in one go.
    // This correctly handles models that output thinking as plain text (not XML tags).
    const reader = aiResponse.body.getReader();
    const decoder = new TextDecoder();
    let fullContent = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      for (const line of chunk.split('\n')) {
        const trimmed = line.trim();
        if (!trimmed || trimmed === 'data: [DONE]') continue;
        if (trimmed.startsWith('data: ')) {
          try {
            const json = JSON.parse(trimmed.slice(6));
            // Accumulate both content and reasoning_content fields
            fullContent += json.choices?.[0]?.delta?.content ?? '';
            fullContent += json.choices?.[0]?.delta?.reasoning_content ?? '';
          } catch {
            // Skip malformed SSE lines
          }
        }
      }
    }

    console.log('\n\n=== RAW AI OUTPUT ===');
    console.log(fullContent);
    console.log('=====================\n\n');

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
