'use client';

import { LayoutGrid, Menu, ChevronDown, Rocket, Home, HeartHandshake, Stethoscope, Plane, User, LogOut, Search, Settings, X, Sparkles } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { useState, useRef, useEffect } from 'react';
import { PILLARS } from '@/lib/constants';
import { createSlug } from '@/lib/utils';
import { motion, AnimatePresence } from 'motion/react';
import { useAuth } from '@/contexts/AuthContext';
import { useChat } from '@/contexts/ChatContext';
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
  const { toggleChat } = useChat();

  // KHÓA CUỘN TRIỆT ĐỂ (html + body)
  useEffect(() => {
    const root = document.documentElement;
    const body = document.body;

    if (isMenuOpen) {
      root.style.overflow = 'hidden';
      body.style.overflow = 'hidden';
      body.style.paddingRight = 'var(--scrollbar-width, 0px)';
    } else {
      root.style.overflow = '';
      body.style.overflow = '';
      body.style.paddingRight = '';
    }
    return () => {
      root.style.overflow = '';
      body.style.overflow = '';
      body.style.paddingRight = '';
    };
  }, [isMenuOpen]);

  const navItems = [
    { title: 'Trang chủ', href: '/', icon: Home, id: 'home' },
    { title: 'Danh mục', icon: LayoutGrid, id: 'catalogue', isMenu: true },
    { title: 'Đối tác', href: '/partner', icon: HeartHandshake, id: 'partner' },
    { title: 'Liên hệ', href: '/contact', icon: Rocket, id: 'contact' },
  ];

  return (
    <>
      <nav className="fixed bottom-6 md:top-6 md:bottom-auto left-0 right-0 z-[1000] px-4 pointer-events-none flex flex-row items-end md:items-start justify-center gap-4">

        {/* Main Navigation Pill - Chuẩn iOS 26 High Contrast */}
        <motion.div
          initial={{ y: 0, opacity: 0 }}
          animate={{
            y: isMenuOpen ? -150 : 0,
            opacity: isMenuOpen ? 0 : 1
          }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
          className={`pointer-events-auto bg-white/85 backdrop-blur-[48px] rounded-full shadow-[0_16px_48px_-12px_rgba(0,0,0,0.15)] ring-1 ring-white/60 flex items-center p-1.5 overflow-visible relative min-w-[280px] md:min-w-[520px] ${isMenuOpen ? 'pointer-events-none' : ''}`}
          onMouseLeave={() => setHoveredTab(null)}
          style={{ willChange: 'transform, opacity' }}
        >
          <div className="flex items-center w-full justify-around px-1 relative">
            <div
              className="relative px-0.5 py-0.5"
              onMouseEnter={() => setHoveredTab('logo')}
            >
              <AnimatePresence initial={false}>
                {hoveredTab === 'logo' && (
                  <motion.div
                    layoutId="active-pill"
                    className="absolute inset-0 rounded-full bg-black/5"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ type: 'spring', stiffness: 450, damping: 45 }}
                    style={{ willChange: 'transform, opacity' }}
                  />
                )}
              </AnimatePresence>
              <Link
                href="/"
                className="flex flex-col items-center gap-1 px-3 md:px-6 py-2 rounded-full relative z-10 transition-transform hover:scale-110 duration-300"
              >
                <div className="size-5 md:size-6 relative flex items-center justify-center mb-0.5">
                  <Image
                    src="/logo.png"
                    alt="Logo"
                    fill
                    className="object-contain"
                    priority
                  />
                </div>
                <span className="hidden md:block text-[9px] md:text-[11px] font-black uppercase tracking-tighter leading-none text-black/40">Sàn DV</span>
              </Link>
            </div>

            {navItems.map((item) => {
              const isActive = (item.isMenu && isMenuOpen) || (!item.isMenu && item.href === pathname);
              const isHovered = hoveredTab === item.id;

              return (
                <div
                  key={item.id}
                  className="relative px-0.5 py-0.5"
                  onMouseEnter={() => setHoveredTab(item.id)}
                >
                  <AnimatePresence initial={false}>
                    {(isHovered || isActive) && (
                      <motion.div
                        layoutId="active-pill"
                        className={`absolute inset-0 rounded-full ${isActive ? 'bg-black/10' : 'bg-black/5'}`}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ type: 'spring', stiffness: 450, damping: 45, mass: 1 }}
                        style={{ willChange: 'transform, opacity' }}
                      />
                    )}
                  </AnimatePresence>

                  {item.isMenu ? (
                    <button
                      onClick={() => setIsMenuOpen(!isMenuOpen)}
                      className={`flex flex-col items-center gap-1 px-3 md:px-7 py-2 rounded-full transition-colors duration-300 relative z-10 cursor-pointer ${isActive ? 'text-black' : 'text-black/50 hover:text-black'}`}
                    >
                      <item.icon size={19} strokeWidth={isActive ? 2.5 : 2} className="mb-0.5" />
                      <span className="hidden md:block text-[9px] md:text-[11px] font-black uppercase tracking-tighter leading-none">{item.title}</span>
                    </button>
                  ) : (
                    <Link
                      href={item.href!}
                      className={`flex flex-col items-center gap-1 px-3 md:px-7 py-2 rounded-full transition-colors duration-300 relative z-10 ${isActive ? 'text-black' : 'text-black/50 hover:text-black'}`}
                    >
                      <item.icon size={19} strokeWidth={isActive ? 2.5 : 2} className="mb-0.5" />
                      <span className="hidden md:block text-[9px] md:text-[11px] font-black uppercase tracking-tighter leading-none">{item.title}</span>
                    </Link>
                  )}
                </div>
              );
            })}

            <div
              className="relative px-0.5 py-0.5"
              onMouseEnter={() => setHoveredTab('user')}
            >
              <AnimatePresence initial={false}>
                {(hoveredTab === 'user' || isUserMenuOpen) && (
                  <motion.div
                    layoutId="active-pill"
                    className={`absolute inset-0 rounded-full ${isUserMenuOpen ? 'bg-black/10' : 'bg-black/5'}`}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ type: 'spring', stiffness: 450, damping: 45 }}
                    style={{ willChange: 'transform, opacity' }}
                  />
                )}
              </AnimatePresence>

              {isLoading ? (
                <div className="size-10 md:size-12 bg-black/5 animate-pulse rounded-full" />
              ) : user ? (
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className={`flex flex-col items-center gap-1 px-3 md:px-7 py-2 rounded-full transition-all duration-300 relative z-10 cursor-pointer ${isUserMenuOpen ? 'text-black' : 'text-black/50 hover:text-black'}`}
                >
                  <User size={19} strokeWidth={isUserMenuOpen ? 2.5 : 2} className="mb-0.5" />
                  <span className="hidden md:block text-[9px] md:text-[11px] font-black uppercase tracking-tighter leading-none text-center">Tôi</span>
                </button>
              ) : (
                <Link
                  href="/login"
                  className="flex flex-col items-center gap-1 px-3 md:px-7 py-2 rounded-full transition-all duration-300 relative z-10 text-black/50 hover:text-black"
                >
                  <User size={19} strokeWidth={2} className="mb-0.5" />
                  <span className="hidden md:block text-[9px] md:text-[11px] font-black uppercase tracking-tighter leading-none">Login</span>
                </Link>
              )}
            </div>
          </div>
        </motion.div>

        {!isMenuOpen && (
          <motion.button
            initial={{ x: 50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 50, opacity: 0 }}
            transition={{ type: "spring", stiffness: 400, damping: 40 }}
            onClick={toggleChat}
            layoutId="chatbot-modal"
            style={{ willChange: "transform, opacity", transform: "translateZ(0)" }}
            className="pointer-events-auto size-[54px] md:size-[64px] rounded-full bg-white/80 backdrop-blur-[32px] text-emerald-500 flex items-center justify-center shadow-[0_12px_44px_rgba(0,0,0,0.12)] hover:scale-110 active:scale-95 transition-all cursor-pointer ring-1 ring-white/60 hover:bg-white/95"
          >
            <motion.div
              layoutId="chatbot-icon"
              className="size-full flex items-center justify-center"
            >
              <Sparkles size={24} className="size-6 md:size-[26px]" strokeWidth={2.2} />
            </motion.div>
          </motion.button>
        )}
      </nav>

      {/* COMPACT MODE: Mega Menu tối ưu không gian & khoảng cách chuẩn quốc tế */}
      <AnimatePresence>
        {isMenuOpen && (
          <div className="fixed inset-0 z-[9999] overflow-y-auto pointer-events-auto bg-white/98 md:bg-white/95 backdrop-blur-[64px] shadow-2xl custom-scrollbar overscroll-behavior-contain">

            <motion.div
              initial={{ y: -50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -50, opacity: 0 }}
              transition={{ type: "spring", bounce: 0.1, duration: 0.5 }}
              className="w-full min-h-full px-6 md:px-16 pt-16 md:pt-20 pb-20 relative"
            >
              <div className="max-w-[1740px] mx-auto">
                {/* Header Menu - Gọn gàng hơn */}
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 md:mb-12 gap-6">
                  <div>
                    <motion.div
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      className="flex items-center gap-3 mb-2 opacity-50"
                    >
                      <Image src="/logo.png" alt="Logo" width={32} height={32} className="object-contain" />
                      <span className="text-sm font-black uppercase tracking-[0.2em]">Sàn Dịch Vụ</span>
                    </motion.div>
                    <motion.h2
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: 0.1 }}
                      className="text-3xl sm:text-4xl md:text-5xl font-black uppercase tracking-tighter text-black mb-1"
                      style={{ fontFamily: 'Manrope, ui-sans-serif, system-ui, sans-serif' }}
                    >
                      Danh mục toàn ngành
                    </motion.h2>
                  </div>

                  <motion.button
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    whileHover={{ scale: 1.1 }}
                    onClick={() => setIsMenuOpen(false)}
                    className="size-12 md:size-14 rounded-full bg-black/5 flex items-center justify-center cursor-pointer hover:bg-red-50 hover:text-red-600 transition-all self-end md:self-center"
                  >
                    <X size={28} />
                  </motion.button>
                </div>

                {/* Grid Nội dung - Thu hẹp Gap & Spacing chuẩn quốc tế */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-x-12 gap-y-10 px-1">
                  {PILLARS.map((pillar, pillarIdx) => {
                    const Icon = iconMap[pillar.id] || Rocket;
                    return (
                      <motion.div
                        key={pillar.id}
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.2 + (pillarIdx * 0.05) }}
                        className="group/pillar bg-black/[0.015] md:bg-transparent p-5 md:p-0 rounded-[28px]"
                      >
                        <div className="flex items-center gap-3 mb-4 md:mb-6">
                          <div className="size-10 md:size-11 rounded-[16px] md:rounded-[18px] bg-black/5 flex items-center justify-center text-black group-hover/pillar:bg-black group-hover/pillar:text-white transition-all duration-300">
                            <Icon size={20} strokeWidth={2.5} />
                          </div>
                          <h4 className="text-[16px] md:text-[17px] font-black uppercase text-black tracking-tighter leading-tight">{pillar.title}</h4>
                        </div>
                        <ul className="space-y-2.5 ml-1 md:ml-0">
                          {pillar.industries.map((ind, idx) => (
                            <li key={idx}>
                              <Link
                                href={`/danh-muc/${createSlug(ind)}`}
                                onClick={() => setIsMenuOpen(false)}
                                className="text-[14px] font-extrabold text-black/50 hover:text-black transition-all flex items-center gap-2.5 group/item hover:translate-x-1 duration-200 leading-normal"
                              >
                                <div className="w-1 h-1 rounded-full bg-black/10 group-hover/item:bg-black transition-all shrink-0" />
                                <span className="flex-1 truncate md:whitespace-normal group-hover:underline underline-offset-4 decoration-black/10 transition-all">{ind}</span>
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isUserMenuOpen && (
          <div className="fixed inset-0 z-[1200] flex items-end md:items-start justify-center pointer-events-none pb-[120px] md:pb-0 md:pt-[120px]">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsUserMenuOpen(false)}
              className="absolute inset-0 bg-black/5 backdrop-blur-sm pointer-events-auto"
            />
            <motion.div
              initial={{ y: -20, opacity: 0, scale: 0.95 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: -20, opacity: 0, scale: 0.95 }}
              className="w-[340px] bg-white/98 backdrop-blur-[64px] rounded-[48px] shadow-2xl p-4 pointer-events-auto mb-4 md:mt-4 ring-1 ring-black/5 overflow-hidden mx-4"
            >
              <div className="p-8 border-b border-black/5 mb-4 rounded-[36px] bg-black/5 text-black">
                <p className="text-base font-black truncate mb-0.5">{user?.user?.full_name || 'Người dùng'}</p>
                <p className="text-sm text-black/50 font-bold tracking-tight">{user?.user?.phone || 'Chưa đăng ký'}</p>
              </div>
              <div className="grid grid-cols-1 gap-2 p-1">
                <Link href="/profile" onClick={() => setIsUserMenuOpen(false)} className="flex items-center justify-between px-7 py-5 hover:bg-black/5 rounded-[32px] group italic transition-all">
                  <div className="flex items-center gap-4 text-[16px] font-black text-black">
                    <User size={18} strokeWidth={2.5} />
                    Hồ sơ của tôi
                  </div>
                  <ChevronDown size={14} className="-rotate-90 text-black/20" />
                </Link>
                <Link href="/admin" onClick={() => setIsUserMenuOpen(false)} className="flex items-center justify-between px-7 py-5 hover:bg-black/5 rounded-[32px] group transition-all">
                  <div className="flex items-center gap-4 text-[16px] font-black text-black">
                    <Settings size={18} strokeWidth={2.5} />
                    Bảng điều khiển
                  </div>
                  <ChevronDown size={14} className="-rotate-90 text-black/20" />
                </Link>
                <button
                  onClick={() => { setIsUserMenuOpen(false); logout(); }}
                  className="w-full flex items-center gap-4 px-7 py-5 bg-red-50/50 hover:bg-red-50 rounded-[32px] text-[16px] font-black text-red-600 transition-all text-left mt-4"
                >
                  <LogOut size={18} strokeWidth={2.5} />
                  Đăng xuất tài khoản
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
