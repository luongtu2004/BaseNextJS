'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { ReactNode, useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { motion, AnimatePresence } from 'motion/react';
import { 
  LayoutGrid, 
  FileText, 
  FolderTree, 
  Users, 
  Boxes, 
  LogOut, 
  ChevronRight,
  ShieldCheck,
  Settings
} from 'lucide-react';

interface AdminLayoutProps {
  children: ReactNode;
}

const navItems = [
  { href: '/admin', label: 'Tổng quan', icon: LayoutGrid, exact: true },
  { href: '/admin/articles', label: 'Bài viết', icon: FileText },
  { href: '/admin/categories', label: 'Danh mục bài viết', icon: FolderTree },
  { href: '/admin/taxonomy', label: 'Ngành nghề & Dịch vụ', icon: Boxes },
  { href: '/admin/users', label: 'Người dùng', icon: Users },
  { href: '/admin/providers', label: 'Nhà cung cấp', icon: ShieldCheck },
];

export default function AdminLayout({ children }: AdminLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, isLoading } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isLoading && mounted) {
      if (!user || !user.roles?.includes('admin')) {
        router.replace('/');
      }
    }
  }, [user, isLoading, mounted, router]);

  if (!mounted || isLoading || !user || !user.roles?.includes('admin')) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <motion.div 
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="size-8 border-4 border-black/10 border-t-black rounded-full"
        />
      </div>
    );
  }

  const isActive = (href: string, exact?: boolean) => {
    if (exact) return pathname === href;
    return pathname.startsWith(href);
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex font-sans text-black selection:bg-black selection:text-white">
      {/* Top Loader Bar */}
      <AnimatePresence>
         {isLoading && (
            <motion.div 
               initial={{ width: 0, opacity: 0 }}
               animate={{ width: '70%', opacity: 1 }}
               exit={{ width: '100%', opacity: 0 }}
               transition={{ duration: 0.5 }}
               className="fixed top-0 left-0 h-1 bg-black z-[200] shadow-[0_0_10px_rgba(0,0,0,0.2)]"
            />
         )}
      </AnimatePresence>

      {/* Sidebar - Chuẩn White Glass */}
      <aside className="fixed left-0 top-0 bottom-0 w-72 bg-white/80 backdrop-blur-[40px] border-r border-black/5 z-[100] flex flex-col p-6">
        <nav className="flex-1 space-y-1 pt-4">
          {navItems.map((item) => {
            const active = isActive(item.href, item.exact);
            return (
              <Link
                key={item.href}
                href={item.href}
                className="relative group block"
              >
                <div className={`flex items-center gap-3 px-4 py-3.5 rounded-[20px] transition-all duration-300 relative z-10 ${
                  active 
                    ? 'text-black font-black' 
                    : 'text-black/40 hover:text-black font-bold'
                }`}>
                  <item.icon size={20} strokeWidth={active ? 2.5 : 2} />
                  <span className="text-[13px] uppercase tracking-tighter">{item.label}</span>
                  {active && (
                    <motion.div 
                      layoutId="active-nav-bg"
                      className="absolute inset-0 bg-black/5 rounded-[20px] -z-10"
                      transition={{ type: 'spring', stiffness: 400, damping: 40 }}
                    />
                  )}
                </div>
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto pt-6 border-t border-black/5 space-y-3">
          <Link 
            href="/"
            className="flex items-center gap-3 px-4 py-3 rounded-[20px] text-black/40 hover:text-black font-bold transition-all text-[13px] uppercase tracking-tighter group/home"
          >
            <div className="size-6 relative flex items-center justify-center filter grayscale group-hover/home:grayscale-0 transition-all opacity-40 group-hover:opacity-100">
              <img src="/logo.png" alt="Logo" className="object-contain" />
            </div>
            Về trang chủ
          </Link>
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-[20px] text-red-500/60 hover:text-red-500 hover:bg-red-50 font-bold transition-all text-[13px] uppercase tracking-tighter"
          >
            <LogOut size={18} />
            Đăng xuất
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 ml-72 min-h-screen">
        <header className="h-20 border-b border-black/5 bg-white/50 backdrop-blur-md flex items-center justify-between px-10 sticky top-0 z-[90]">
          <div className="flex items-center gap-2 text-black/40 font-bold text-xs uppercase tracking-widest">
            <span>Admin</span>
            <ChevronRight size={14} />
            <span className="text-black">{navItems.find(i => isActive(i.href, i.exact))?.label || 'Tổng quan'}</span>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-black leading-none">{user?.user?.full_name}</p>
              <p className="text-[10px] font-bold text-black/40 uppercase tracking-tighter mt-1">Administrator</p>
            </div>
            <div className="size-10 rounded-full bg-black/5 border border-black/5 flex items-center justify-center font-black text-xs">
              {user?.user?.full_name?.charAt(0)}
            </div>
          </div>
        </header>

        <div className="p-10">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ y: 10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -10, opacity: 0 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
