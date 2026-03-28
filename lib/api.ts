import Cookies from 'js-cookie';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/** Lấy token đã lưu trong Cookies */
export function getToken(): string | undefined {
  if (typeof window === 'undefined') return undefined;
  return Cookies.get('access_token');
}

/** Lưu token vào Cookies */
export function setToken(token: string): void {
  Cookies.set('access_token', token, { expires: 7, path: '/' }); // 7 days
}

/** Xóa token (logout) */
export function clearToken(): void {
  Cookies.remove('access_token', { path: '/' });
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
