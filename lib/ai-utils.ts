/**
 * AI Response Processing Utilities
 */

/**
 * Strips thinking/reasoning tags or prefixes from AI response text.
 * Handles <think>, <thinking>, and "Thinking Process:" markers.
 */
export function stripThinking(text: string): string {
  let result = text;

  // 1. Tags like <think>...</think> (DeepSeek, QwQ)
  if (result.toLowerCase().includes('</think>')) {
    const parts = result.split(/<\/think>/i);
    result = parts[parts.length - 1];
    return result.trim();
  }

  // 2. Tags like <thinking>...</thinking> (XML style)
  if (result.toLowerCase().includes('</thinking>')) {
    const parts = result.split(/<\/thinking>/i);
    result = parts[parts.length - 1];
    return result.trim();
  }

  // 3. Text markers like "Thinking Process:" (Qwen 7B etc.)
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
