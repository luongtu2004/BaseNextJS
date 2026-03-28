'use client';

import { LayoutGrid, Menu, ChevronDown, Rocket, Home, HeartHandshake, Stethoscope, Plane, User, LogOut, Search, Settings, X } from 'lucide-react';
import Link from 'next/link';
import { useState, useRef, useEffect } from 'react';
import { PILLARS } from '@/lib/constants';
import { createSlug } from '@/lib/utils';
import { motion, AnimatePresence } from 'motion/react';
import { useAuth } from '@/contexts/AuthContext';
import { usePathname } from 'next/navigation';

const iconMap: Record<string, any> = {
  transportation: Rocket,
  construction_electronics: Home,
  housekeeping_beauty: HeartHandshake,
  education: Stethoscope,
  travel: Plane,
};

export default function Navbar() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [hoveredTab, setHoveredTab] = useState<string | null>(null);
  const { user, isLoading, logout } = useAuth();

  const navItems = [
    { title: 'Trang chủ', href: '/', icon: Home, id: 'home' },
    { title: 'Danh mục', icon: LayoutGrid, id: 'catalogue', isMenu: true },
    { title: 'Đối tác', href: '/partner', icon: HeartHandshake, id: 'partner' },
    { title: 'Liên hệ', href: '/contact', icon: Rocket, id: 'contact' },
  ];

  return (
    <>
      <nav className="fixed top-6 left-0 right-0 z-[1000] px-4 pointer-events-none flex justify-center items-start gap-4">

        {/* Main Navigation Pill - Chuẩn iOS 26 "Thủy tinh trắng" */}
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 20 }}
          className="pointer-events-auto bg-white/80 backdrop-blur-[48px] rounded-full shadow-[0_12px_44px_rgba(0,0,0,0.12)] ring-1 ring-white/60 flex items-center p-1.5 overflow-visible relative min-w-[360px] md:min-w-[480px]"
          onMouseLeave={() => setHoveredTab(null)}
        >
          <div className="flex items-center w-full justify-around px-1 relative">
            {navItems.map((item) => {
              const isActive = item.isMenu ? isMenuOpen : pathname === item.href;
              const isHovered = hoveredTab === item.id;

              return (
                <div
                  key={item.id}
                  className="relative px-1 py-1"
                  onMouseEnter={() => setHoveredTab(item.id)}
                >
                  {/* Sliding Pill Highlight (iOS Style) */}
                  <AnimatePresence>
                    {(isHovered || isActive) && (
                      <motion.div
                        layoutId="active-pill"
                        className={`absolute inset-0 rounded-full ${isActive ? 'bg-black/10' : 'bg-black/5'}`}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                      />
                    )}
                  </AnimatePresence>

                  {item.isMenu ? (
                    <button
                      onClick={() => setIsMenuOpen(!isMenuOpen)}
                      className={`flex flex-col items-center gap-1.5 px-4 md:px-7 py-2.5 rounded-full transition-colors duration-300 relative z-10 cursor-pointer ${isActive ? 'text-black' : 'text-black/60 hover:text-black'}`}
                    >
                      <item.icon size={20} strokeWidth={isActive ? 2.5 : 2} className="transition-transform duration-300" />
                      <span className="text-[10px] md:text-[11px] font-black uppercase tracking-tighter leading-none">{item.title}</span>
                    </button>
                  ) : (
                    <Link
                      href={item.href!}
                      className={`flex flex-col items-center gap-1.5 px-4 md:px-7 py-2.5 rounded-full transition-colors duration-300 relative z-10 ${isActive ? 'text-black' : 'text-black/60 hover:text-black'}`}
                    >
                      <item.icon size={20} strokeWidth={isActive ? 2.5 : 2} className="transition-transform duration-300" />
                      <span className="text-[10px] md:text-[11px] font-black uppercase tracking-tighter leading-none">{item.title}</span>
                    </Link>
                  )}
                </div>
              );
            })}

            {/* User Account / Profile */}
            <div
              className="relative px-1 py-1"
              onMouseEnter={() => setHoveredTab('user')}
            >
              <AnimatePresence>
                {(hoveredTab === 'user' || isUserMenuOpen) && (
                  <motion.div
                    layoutId="active-pill"
                    className={`absolute inset-0 rounded-full ${isUserMenuOpen ? 'bg-black/10' : 'bg-black/5'}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                  />
                )}
              </AnimatePresence>

              {isLoading ? (
                <div className="size-10 bg-black/5 animate-pulse rounded-full" />
              ) : user ? (
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className={`flex flex-col items-center gap-1.5 px-4 md:px-7 py-2.5 rounded-full transition-all duration-300 relative z-10 cursor-pointer ${isUserMenuOpen ? 'text-black' : 'text-black/60 hover:text-black'}`}
                >
                  <User size={20} strokeWidth={isUserMenuOpen ? 2.5 : 2} />
                  <span className="text-[10px] md:text-[11px] font-black uppercase tracking-tighter leading-none">Tôi</span>
                </button>
              ) : (
                <Link
                  href="/login"
                  className="flex flex-col items-center gap-1.5 px-4 md:px-7 py-2.5 rounded-full transition-all duration-300 relative z-10 text-black/60 hover:text-black"
                >
                  <User size={20} strokeWidth={2} />
                  <span className="text-[10px] md:text-[11px] font-black uppercase tracking-tighter leading-none">Login</span>
                </Link>
              )}
            </div>
          </div>
        </motion.div>

        {/* Separate Utility Capsule (Search) - iOS High Contrast */}
        <motion.button
          initial={{ x: 50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 20, delay: 0.1 }}
          className="pointer-events-auto size-[54px] md:size-[64px] rounded-full bg-white/90 backdrop-blur-[32px] text-black flex items-center justify-center shadow-[0_12px_44px_rgba(0,0,0,0.12)] hover:scale-105 transition-transform active:scale-95 cursor-pointer ring-1 ring-white/60"
        >
          <Search size={24} strokeWidth={2.5} />
        </motion.button>
      </nav>

      {/* Full-Width Mega Menu (Tràn màn hình) */}
      <AnimatePresence>
        {isMenuOpen && (
          <div className="fixed inset-0 z-[990] flex items-start justify-center pointer-events-none">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMenuOpen(false)}
              className="absolute inset-0 bg-white/20 backdrop-blur-md pointer-events-auto"
            />

            <motion.div
              initial={{ y: -100, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -100, opacity: 0 }}
              transition={{ type: "spring", bounce: 0, duration: 0.5 }}
              className="w-full bg-white/95 backdrop-blur-[48px] shadow-2xl pt-[120px] pb-16 px-6 md:px-16 pointer-events-auto max-h-[92vh] overflow-y-auto border-b border-black/5"
            >
              <div className="max-w-[1740px] mx-auto">
                <div className="flex items-center justify-between mb-12">
                  <div>
                    <h2 className="text-4xl md:text-5xl font-black uppercase tracking-tighter text-black mb-2" style={{ fontFamily: 'Manrope, ui-sans-serif, system-ui, sans-serif' }}>Danh mục toàn ngành</h2>
                    <p className="text-black/50 font-bold uppercase tracking-widest text-[12px]">Khám phá giải pháp dịch vụ chuyên biệt</p>
                  </div>
                  <button onClick={() => setIsMenuOpen(false)} className="size-14 rounded-full bg-black/5 flex items-center justify-center cursor-pointer hover:bg-black/10 transition-colors">
                    <X size={28} className="text-black" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-10">
                  {PILLARS.map((pillar) => {
                    const Icon = iconMap[pillar.id] || Rocket;
                    return (
                      <div key={pillar.id} className="group/pillar">
                        <div className="flex items-center gap-4 mb-8">
                          <div className="size-14 rounded-2xl bg-black/5 flex items-center justify-center text-black shadow-sm group-hover/pillar:bg-black group-hover/pillar:text-white transition-all duration-300">
                            <Icon size={26} strokeWidth={2.5} />
                          </div>
                          <h4 className="text-[18px] font-black uppercase text-black tracking-tighter leading-tight">{pillar.title}</h4>
                        </div>
                        <ul className="space-y-4">
                          {pillar.industries.map((ind, idx) => (
                            <li key={idx}>
                              <Link
                                href={`/danh-muc/${createSlug(ind)}`}
                                onClick={() => setIsMenuOpen(false)}
                                className="text-[16px] font-bold text-black/50 hover:text-black transition-all flex items-center gap-3 group/item translate-x-0 hover:translate-x-2 duration-300"
                              >
                                <div className="w-1.5 h-1.5 rounded-full bg-black/10 group-hover/item:bg-black transition-all" />
                                {ind}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* User Account Dropdown (Below top pill) */}
      <AnimatePresence>
        {isUserMenuOpen && (
          <div className="fixed inset-0 z-[990] flex items-start justify-center pointer-events-none pt-[100px]">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsUserMenuOpen(false)}
              className="absolute inset-0 bg-transparent pointer-events-auto"
            />
            <motion.div
              initial={{ y: -20, opacity: 0, scale: 0.95 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: -20, opacity: 0, scale: 0.95 }}
              className="w-[320px] bg-white/95 backdrop-blur-[48px] rounded-[32px] shadow-2xl p-3 pointer-events-auto mt-4 ring-1 ring-black/5 overflow-hidden"
            >
              <div className="p-6 border-b border-black/5 mb-3 rounded-[24px] bg-black/5 text-black">
                <p className="text-sm font-black truncate">{user?.user?.full_name}</p>
                <p className="text-xs text-black/50 font-bold tracking-tight truncate">{user?.user?.phone}</p>
              </div>
              <div className="grid grid-cols-1 gap-1">
                <Link href="/profile" onClick={() => setIsUserMenuOpen(false)} className="flex items-center gap-4 px-6 py-4 hover:bg-black/5 rounded-2xl text-[15px] font-black text-black transition-all">
                  <User size={18} strokeWidth={2.5} />
                  Hồ sơ cá nhân
                </Link>
                <Link href="/admin" onClick={() => setIsUserMenuOpen(false)} className="flex items-center gap-4 px-6 py-4 hover:bg-black/5 rounded-2xl text-[15px] font-black text-black transition-all">
                  <Settings size={18} strokeWidth={2.5} />
                  Bảng điều khiển
                </Link>
                <button
                  onClick={() => { setIsUserMenuOpen(false); logout(); }}
                  className="w-full flex items-center gap-4 px-6 py-4 hover:bg-red-50 rounded-2xl text-[15px] font-black text-red-600 transition-all text-left"
                >
                  <LogOut size={18} strokeWidth={2.5} />
                  Đăng xuất
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
