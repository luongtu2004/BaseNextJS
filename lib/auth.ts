import { fetchAPI, setToken, clearToken } from './api';

export interface UserSession {
  id: string;
  phone: string;
  full_name: string;
  gender?: string | number;
  dob?: string;
  avatar_url?: string;
  phone_verified?: boolean;
  status?: string;
  roles: string[];
  profile?: {
    bio?: string;
    preferred_language?: string;
    timezone?: string;
  };
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
