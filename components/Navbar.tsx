'use client';

import { LayoutGrid, Menu, ChevronDown, Rocket, Home, HeartHandshake, Stethoscope, Plane } from 'lucide-react';
import Link from 'next/link';
import { useState, useRef, useEffect } from 'react';
import { PILLARS } from '@/lib/constants';
import { createSlug } from '@/lib/utils';
import { motion, AnimatePresence } from 'motion/react';

const iconMap: Record<string, any> = {
  transportation: Rocket,
  construction_electronics: Home,
  housekeeping_beauty: HeartHandshake,
  education: Stethoscope,
  travel: Plane,
};

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

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

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
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
          <button className="btn-primary-gradient px-6 py-2 rounded-full text-[13px] font-semibold transition-all cursor-pointer shadow-sm hover:brightness-105">
            Đặt dịch vụ
          </button>
          <button className="md:hidden text-slate-900">
            <Menu size={24} />
          </button>
        </div>
      </div>
    </nav>
  );
}
