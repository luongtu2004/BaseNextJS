import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Giải mã JWT Payload mà không cần thư viện ngoài (Base64)
function parseJwt(token: string) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

const guestOnlyRoutes = ['/login', '/register'];
const protectedRoutes = ['/profile'];
const adminRoutes = ['/admin'];

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;
  const { pathname } = request.nextUrl;

  // 1. Chặn người dùng đã đăng nhập vào trang Login/Register
  if (guestOnlyRoutes.some(route => pathname.startsWith(route))) {
    if (token) {
      return NextResponse.redirect(new URL('/', request.url));
    }
  }

  // 2. Chặn truy cập Admin nếu không có quyền
  if (adminRoutes.some(route => pathname.startsWith(route))) {
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
    
    const payload = parseJwt(token);
    const roles = payload?.roles || [];
    
    if (!roles.includes('admin')) {
      // Nếu không phải admin, đẩy về trang chủ
      return NextResponse.redirect(new URL('/', request.url));
    }
  }

  // 3. Chặn các route bảo mật khác
  if (protectedRoutes.some(route => pathname.startsWith(route))) {
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
