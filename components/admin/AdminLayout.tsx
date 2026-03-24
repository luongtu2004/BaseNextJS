import Link from 'next/link';
import { ReactNode } from 'react';

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-md">
        <div className="p-4 border-b">
          <h2 className="text-xl font-bold">Quản trị viên</h2>
        </div>
        <nav className="p-4">
          <ul className="space-y-2">
            <li>
              <Link href="/admin" className="block py-2 px-4 rounded hover:bg-gray-100">
                Tổng quan
              </Link>
            </li>
            <li>
              <Link href="/admin/articles" className="block py-2 px-4 rounded hover:bg-gray-100">
                Bài viết
              </Link>
            </li>
            <li>
              <Link href="/admin/categories" className="block py-2 px-4 rounded hover:bg-gray-100">
                Danh mục
              </Link>
            </li>
            <li>
              <Link href="/admin/users" className="block py-2 px-4 rounded hover:bg-gray-100">
                Người dùng
              </Link>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
