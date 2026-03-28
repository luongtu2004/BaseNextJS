import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Danh sách các route chỉ dành cho người chưa đăng nhập (khách)
const guestOnlyRoutes = ['/login', '/register'];

// Danh sách các route yêu cầu đăng nhập
const protectedRoutes = ['/admin', '/profile'];

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;
  const { pathname } = request.nextUrl;

  // 1. Nếu đang vào trang Auth nhưng ĐÃ CÓ token -> Chặn, đẩy về Home/Dashboard
  if (guestOnlyRoutes.some(route => pathname.startsWith(route))) {
    if (token) {
      return NextResponse.redirect(new URL('/', request.url));
    }
  }

  // 2. Nếu đang vào trang Bảo mật mà CHƯA CÓ token -> Chặn, đẩy về Login
  if (protectedRoutes.some(route => pathname.startsWith(route))) {
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  return NextResponse.next();
}

// Cấu hình matcher để middleware không chạy với tất cả static files
export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
