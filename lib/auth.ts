import { fetchAPI, setToken, clearToken } from './api';

export interface UserSession {
  user: {
    id: string;
    phone: string;
    full_name: string;
    gender?: string;
    dob?: string;
    avatar_url?: string;
    phone_verified: boolean;
    status: string;
  };
  roles: string[];
}

/**
 * Lấy thông tin session hiện tại
 */
export async function getSession(): Promise<UserSession | null> {
  try {
    const data = await fetchAPI<UserSession>('/api/v1/common/me');
    return data;
  } catch (error) {
    return null;
  }
}

/**
 * Xử lý đăng xuất chung
 */
export function handleLogout(callback?: () => void) {
  clearToken();
  if (callback) callback();
}
