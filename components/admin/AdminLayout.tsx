'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode, useEffect, useState } from 'react';
import { getToken } from '@/lib/api';

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
  const [hasToken, setHasToken] = useState(false);
  const [tokenInput, setTokenInput] = useState('');
  const [showTokenPrompt, setShowTokenPrompt] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (token) {
      setHasToken(true);
    } else {
      setShowTokenPrompt(true);
    }
  }, []);

  const handleSaveToken = () => {
    if (tokenInput.trim()) {
      localStorage.setItem('access_token', tokenInput.trim());
      setHasToken(true);
      setShowTokenPrompt(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setHasToken(false);
    setShowTokenPrompt(true);
  };

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
                  className={`flex items-center gap-2 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                    isActive(item.href, item.exact)
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
          {hasToken ? (
            <button
              onClick={handleLogout}
              className="w-full text-xs text-red-500 hover:text-red-700 py-1"
            >
              🔓 Đăng xuất / Đổi token
            </button>
          ) : null}
          <Link href="/" className="block text-xs text-gray-400 hover:text-gray-600 mt-2 text-center">
            ← Về trang chủ
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto relative">
        {/* Token prompt overlay */}
        {showTokenPrompt && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
            <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md mx-4">
              <h3 className="text-lg font-bold mb-2">🔑 Nhập Admin Token</h3>
              <p className="text-sm text-gray-500 mb-4">
                Đăng nhập tại <code className="bg-gray-100 px-1 rounded">/api/v1/auth/login/password</code> để lấy access_token, rồi dán vào đây.
              </p>
              <textarea
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                className="w-full border rounded-lg p-3 text-sm font-mono h-24 resize-none focus:ring-2 focus:ring-blue-500 outline-none"
              />
              <button
                onClick={handleSaveToken}
                disabled={!tokenInput.trim()}
                className="w-full mt-3 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg disabled:opacity-40"
              >
                Xác nhận & Tiếp tục
              </button>
            </div>
          </div>
        )}

        {children}
      </main>
    </div>
  );
}
