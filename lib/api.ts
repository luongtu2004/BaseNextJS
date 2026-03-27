const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/** Lấy token đã lưu trong localStorage */
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

/** Lưu token vào localStorage */
export function setToken(token: string): void {
  localStorage.setItem('access_token', token);
}

/** Xóa token (logout) */
export function clearToken(): void {
  localStorage.removeItem('access_token');
}

interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

/**
 * Gọi API backend, tự động gắn Authorization header nếu có token.
 * Ném Error nếu response không OK.
 */
export async function fetchAPI<T = unknown>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { skipAuth = false, ...rest } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(rest.headers as Record<string, string> | undefined),
  };

  if (!skipAuth) {
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers,
  });

  if (!res.ok) {
    let message = `API error ${res.status}`;
    try {
      const err = await res.json();
      message = err?.detail || err?.message || message;
    } catch { /* ignore */ }
    throw new Error(message);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
