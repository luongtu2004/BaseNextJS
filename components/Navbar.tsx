'use client';

import { LayoutGrid, Menu, ChevronDown, Rocket, Home, HeartHandshake, Stethoscope, Plane, User, LogOut } from 'lucide-react';
import Link from 'next/link';
import { useState, useRef, useEffect } from 'react';
import { PILLARS } from '@/lib/constants';
import { createSlug } from '@/lib/utils';
import { motion, AnimatePresence } from 'motion/react';
import { useAuth } from '@/contexts/AuthContext';

const iconMap: Record<string, any> = {
  transportation: Rocket,
  construction_electronics: Home,
  housekeeping_beauty: HeartHandshake,
  education: Stethoscope,
  travel: Plane,
};

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const { user, isLoading, logout } = useAuth();

  const handleOpen = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setIsMenuOpen(true);
  };

  const handleClose = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setIsMenuOpen(false);
    }, 150);
  };

  // Close user menu on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.user-dropdown-container')) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <nav className="relative z-[1000] bg-surface/80 backdrop-blur-[20px] h-16">
      <div className="max-w-[1740px] mx-auto px-4 md:px-8 h-full flex items-center justify-between relative">
        <div className="flex items-center gap-10">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="size-9 bg-on-surface rounded-xl flex items-center justify-center text-white group-hover:bg-primary transition-colors duration-300">
              <LayoutGrid size={20} />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900 uppercase">Sàn Dịch Vụ</span>
          </Link>
          
          <div className="hidden md:flex items-center gap-8 h-full">
            <Link href="/" className="text-[13px] font-medium text-slate-500 hover:text-slate-900 transition-colors">Trang chủ</Link>
            
            {/* Mega Menu Trigger Container - Removed 'relative' to allow center positioning against navbar */}
            <div
              className="h-full flex items-center"
              onMouseEnter={handleOpen}
              onMouseLeave={handleClose}
            >
              <button
                className={`flex items-center gap-1.5 text-[13px] font-medium transition-all cursor-pointer h-full px-2 ${isMenuOpen ? 'text-primary' : 'text-slate-500 hover:text-slate-900'}`}
              >
                Danh mục <ChevronDown size={14} className={`transition-transform duration-300 ${isMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Mega Menu Content - Positioned absolutely relative to the max-w container */}
              <AnimatePresence>
                {isMenuOpen && (
                  <div
                    className="absolute top-16 left-1/2 -translate-x-1/2 w-full max-w-[1740px] z-[1001] pt-0 px-4 md:px-8"
                    onMouseEnter={handleOpen}
                    onMouseLeave={handleClose}
                  >
                    {/* Interaction Bridge */}
                    <div className="absolute top-[-10px] left-0 right-0 h-[10px] bg-transparent" />
                    
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      transition={{ duration: 0.2, ease: "easeOut" }}
                      className="bg-surface/85 backdrop-blur-[24px] rounded-3xl shadow-[0_18px_56px_rgba(26,28,31,0.12)] ghost-border p-12 overflow-visible"
                    >
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-start">
                        {PILLARS.map((pillar, index) => {
                          const Icon = iconMap[pillar.id] || Rocket;
                          const shouldCenterLastCard =
                            PILLARS.length % 3 === 2 && index === PILLARS.length - 1;
                          return (
                            <div
                              key={pillar.id}
                              className={`group/pillar bg-surface-container-low rounded-2xl ghost-border p-5 ${shouldCenterLastCard ? 'lg:col-start-2' : ''}`}
                            >
                              <div className="flex items-center gap-3 mb-4">
                                <div className="size-10 rounded-xl bg-surface-container-lowest flex items-center justify-center text-on-surface-variant group-hover/pillar:bg-primary-fixed-dim/30 group-hover/pillar:text-primary transition-all duration-300 shadow-sm ghost-border">
                                  <Icon size={20} />
                                </div>
                                <h4 className="text-[14px] font-bold text-slate-900 tracking-tight uppercase">{pillar.title}</h4>
                              </div>
                              
                              <ul className="grid grid-cols-1 gap-y-2 pl-1">
                                {pillar.industries.map((ind, idx) => (
                                  <li key={idx} className="flex items-start gap-2 group/item">
                                    <div className="mt-[7px] w-1 h-1 rounded-full bg-slate-200 group-hover/item:bg-primary transition-colors shrink-0" />
                                    <Link
                                      href={`/danh-muc/${createSlug(ind)}`}
                                      className="text-[13px] text-slate-500 hover:text-primary transition-colors leading-tight"
                                      title={ind}
                                    >
                                      {ind}
                                    </Link>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          );
                        })}
                      </div>
                    </motion.div>
                  </div>
                )}
              </AnimatePresence>
            </div>

            <Link href="#" className="text-[13px] font-medium text-slate-500 hover:text-slate-900 transition-colors">Trở thành đối tác</Link>
            <Link href="#" className="text-[13px] font-medium text-slate-500 hover:text-slate-900 transition-colors">Liên hệ</Link>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {isLoading ? (
            <div className="h-9 w-24 bg-slate-200 animate-pulse rounded-full" />
          ) : user ? (
            <div className="relative user-dropdown-container">
              <button
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center gap-2 btn-primary-gradient px-5 py-2 rounded-full text-[13px] font-semibold transition-all cursor-pointer shadow-sm hover:brightness-105 text-white"
              >
                <User size={16} />
                <span className="max-w-[100px] truncate">{user.user?.full_name || 'Tài khoản'}</span>
                <ChevronDown size={14} className={`transition-transform duration-300 ${isUserMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              <AnimatePresence>
                {isUserMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.1 } }}
                    className="absolute right-0 top-full mt-2 w-56 bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-slate-100 py-2 overflow-hidden z-[1002]"
                  >
                    <div className="px-4 py-3 border-b border-slate-100 mb-1">
                      <p className="text-sm font-bold text-slate-900 truncate">{user.user?.full_name}</p>
                      <p className="text-xs text-slate-500 truncate">{user.user?.phone}</p>
                    </div>
                    <Link href="/admin" onClick={() => setIsUserMenuOpen(false)} className="flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50 text-sm font-medium text-slate-700 transition-colors">
                      <LayoutGrid size={16} className="text-slate-400" />
                      Bảng điều khiển
                    </Link>
                    <Link href="/profile" onClick={() => setIsUserMenuOpen(false)} className="flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50 text-sm font-medium text-slate-700 transition-colors">
                      <User size={16} className="text-slate-400" />
                      Hồ sơ cá nhân
                    </Link>
                    <div className="h-[1px] bg-slate-100 my-1"></div>
                    <button
                      onClick={() => { setIsUserMenuOpen(false); logout(); }}
                      className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-red-50 text-sm font-medium text-red-600 transition-colors"
                    >
                      <LogOut size={16} />
                      Đăng xuất
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <Link href="/login" className="btn-primary-gradient px-6 py-2 rounded-full text-[13px] font-semibold transition-all cursor-pointer shadow-sm hover:brightness-105 text-white">
              Đăng nhập
            </Link>
          )}
          <button className="md:hidden text-slate-900">
            <Menu size={24} />
          </button>
        </div>
      </div>
    </nav>
  );
}
