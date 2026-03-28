'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface AdminLayoutProps {
  children: ReactNode;
}

const navItems = [
  { href: '/admin', label: 'Tổng quan', icon: '📊', exact: true },
  { href: '/admin/articles', label: 'Bài viết', icon: '📝' },
  { href: '/admin/categories', label: 'Danh mục bài viết', icon: '🗂️' },
  { href: '/admin/taxonomy', label: 'Ngành nghề & Dịch vụ', icon: '🏗️' },
  { href: '/admin/users', label: 'Người dùng', icon: '👥' },
  { href: '/admin/providers', label: 'Nhà cung cấp', icon: '🏢' },
];

export default function AdminLayout({ children }: AdminLayoutProps) {
  const pathname = usePathname();
  const { user, logout, isLoading } = useAuth();

  const isActive = (href: string, exact?: boolean) => {
    if (exact) return pathname === href;
    return pathname.startsWith(href);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-md flex flex-col">
        <div className="p-4 border-b bg-gradient-to-r from-blue-600 to-blue-700">
          <h2 className="text-xl font-bold text-white">⚙️ Quản trị</h2>
          <p className="text-blue-200 text-xs mt-1">Sàn Dịch Vụ Admin</p>
        </div>

        <nav className="p-4 flex-1">
          <ul className="space-y-1">
            {navItems.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-2 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${isActive(item.href, item.exact)
                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                    : 'text-gray-700 hover:bg-gray-100'
                    }`}
                >
                  <span>{item.icon}</span>
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="p-4 border-t">
          {user ? (
            <button
              onClick={logout}
              className="w-full text-xs text-red-500 hover:text-red-700 py-1 font-medium"
            >
              🔓 Đăng xuất
            </button>
          ) : (
            <div className="w-full text-xs text-yellow-500 py-1 text-center font-medium">
              {isLoading ? 'Đang kiểm tra...' : 'Bạn chưa đăng nhập'}
            </div>
          )}
          <Link href="/" className="block text-xs text-gray-400 hover:text-gray-600 mt-2 text-center">
            ← Về trang chủ
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto relative">
        {children}
      </main>
    </div>
  );
}
