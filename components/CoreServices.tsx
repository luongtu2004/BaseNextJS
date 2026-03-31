'use client';

import { useEffect, useState, useRef } from 'react';
import { ChevronRight, Rocket, Home, HeartHandshake, Stethoscope, Plane } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { createSlug } from '@/lib/utils';
import { motion, useScroll, useTransform } from 'motion/react';
import TypingText from './TypingText';
import { fetchAPI } from '@/lib/api';

const iconMap: Record<string, any> = {
  vantaidichuyen: Rocket,
  xaydungnoithat: Home,
  giupvieclamdep: HeartHandshake,
  ytegioduc: Stethoscope,
  dulichbaohiem: Plane,
  // Add fallback for common codes
  transportation: Rocket,
  construction: Home,
  housekeeping: HeartHandshake,
  education: Stethoscope,
  travel: Plane,
};

interface Pillar {
  id: string;
  title: string;
  slug: string;
  description: string;
  image: string;
  industries: string[];
}

export default function CoreServices() {
  const [pillars, setPillars] = useState<Pillar[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const containerRef = useRef(null);

  useEffect(() => {
    async function loadServices() {
      try {
        const data = await fetchAPI<any[]>('/api/v1/customer/industry-categories');
        if (data) {
          const mapped = data.map((item: any) => ({
            id: item.code || item.id,
            title: item.name,
            slug: item.slug,
            description: item.description || 'Hệ sinh thái dịch vụ chuyên nghiệp.',
            image: item.icon_url || 'https://images.unsplash.com/photo-1581094794329-c8112a89af12?q=80&w=2070&auto=format&fit=crop',
            industries: item.service_categories?.map((s: any) => s.name) || []
          }));
          setPillars(mapped);
        }
      } catch (err) {
        console.error('Failed to load services:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadServices();
  }, []);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  const scale = useTransform(scrollYProgress, [0, 0.4, 0.6, 1], [0.85, 1, 1, 0.85]);
  const y = useTransform(scrollYProgress, [0, 0.4, 0.6, 1], [100, 0, 0, -100]);
  const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);

  return (
    <section id="services" ref={containerRef} className="py-20 bg-surface overflow-hidden">
      <div className="max-w-[1740px] mx-auto px-6 md:px-12">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-x-12 gap-y-8 mb-40 border-b border-black/5 pb-16">
          <div className="flex flex-col md:flex-row md:items-center gap-x-10 gap-y-4">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 0.6, x: 0 }}
              viewport={{ once: true }}
              className="text-primary font-black tracking-[0.3em] uppercase text-[12px] md:text-[14px] whitespace-nowrap"
            >
              Hệ sinh thái chính
            </motion.div>
            <div className="hidden md:block w-[1px] h-8 bg-black/10" />
            <motion.h2
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="text-[28px] md:text-[42px] font-black text-primary tracking-[-0.04em] uppercase leading-none"
              style={{ fontFamily: 'Manrope, ui-sans-serif, system-ui, sans-serif' }}
            >
              {pillars.length} Trụ Cột Dịch Vụ
            </motion.h2>
          </div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="max-w-xl"
          >
            <p className="text-[18px] md:text-[22px] text-[#5d4037] font-medium leading-tight tracking-tight italic opacity-80">
              "Sự hội tụ của 45 ngành nghề dịch vụ chuyên nghiệp, đáp ứng mọi khía cạnh trong cuộc sống của bạn."
            </p>
          </motion.div>
        </div>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="size-10 border-4 border-black/10 border-t-black rounded-full animate-spin" />
            <p className="text-[11px] font-black uppercase tracking-widest text-black/20">Đang tải danh mục dịch vụ...</p>
          </div>
        ) : pillars.length === 0 ? (
          <div className="text-center py-20 text-[11px] font-black uppercase tracking-widest text-black/20">
            Chưa có danh mục dịch vụ nào được cấu hình.
          </div>
        ) : (
          <div className="space-y-32">
            {pillars.map((pillar, index) => {
              const Icon = iconMap[pillar.id] || Rocket;
              const isEven = index % 2 === 0;

              return (
                <motion.div
                  key={pillar.id}
                  initial={{ opacity: 0, y: 100, scale: 0.8, rotateX: 10 }}
                  whileInView={{ opacity: 1, y: 0, scale: 1, rotateX: 0 }}
                  viewport={{ once: true, margin: "-100px" }}
                  transition={{ 
                    duration: 1.2, 
                    ease: [0.22, 1, 0.36, 1], 
                    delay: 0.1 
                  }}
                  className={`flex flex-col lg:flex-row items-center gap-12 lg:gap-24 ${isEven ? 'lg:flex-row' : 'lg:flex-row-reverse'}`}
                  style={{ perspective: "1500px" }}
                >
                  {/* Text Content Column */}
                  <div className="flex-1 space-y-8">
                    <div className="flex items-center gap-4">
                      <span className="text-[14px] font-black text-primary/40 uppercase tracking-widest">
                        {index + 1 < 10 ? `0${index + 1}` : index + 1}
                      </span>
                      <div className="h-[1px] w-12 bg-primary/20" />
                    </div>

                    <div className="flex items-center gap-5">
                      <div className="size-16 rounded-2xl bg-primary/10 flex items-center justify-center text-primary shadow-sm border border-primary/5">
                        <Icon size={32} />
                      </div>
                      <div>
                        <h3 className="text-[32px] md:text-[42px] font-black text-primary tracking-[-0.04em] leading-[1.1] uppercase">
                          {pillar.title}
                        </h3>
                      </div>
                    </div>
                    <p className="text-[17px] md:text-[20px] text-[#5d4037] font-bold leading-normal max-w-xl mt-8 mb-12 uppercase tracking-wide opacity-90 transition-opacity">
                      {pillar.description}
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6 max-w-2xl border-l-2 border-primary/5 pl-8">
                      {pillar.industries.slice(0, 10).map((ind, idx) => (
                        <motion.div
                          key={idx}
                          whileHover={{ x: 6, color: "#000" }}
                          className="flex items-start gap-4 text-[14px] text-black/50 font-black uppercase tracking-tight group/item cursor-default transition-all"
                        >
                          <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary/20 group-hover/item:bg-primary group-hover/item:scale-150 transition-all shrink-0" />
                          <span className="leading-tight group-hover/item:tracking-wider transition-all">{ind}</span>
                        </motion.div>
                      ))}
                      {pillar.industries.length > 10 && (
                        <div className="text-[11px] font-black text-primary/30 uppercase tracking-[0.2em] pt-2">
                          + {pillar.industries.length - 10} dịch vụ chuyên sâu khác
                        </div>
                      )}
                    </div>

                    <Link
                      href={`/danh-muc/${pillar.slug}`}
                      className="inline-flex items-center gap-4 text-[16px] font-black text-slate-900 group/btn hover:text-primary transition-all pt-8"
                    >
                      <div className="size-12 rounded-full bg-slate-100 flex items-center justify-center group-hover/btn:bg-primary group-hover/btn:text-white transition-all duration-500 shadow-sm">
                        <ChevronRight size={24} />
                      </div>
                      <span>CHI TIẾT DỊCH VỤ</span>
                    </Link>
                  </div>

                  <div className="flex-1 relative group flex items-center justify-center w-full">
                    <motion.div
                      whileHover={{ scale: 1.05, rotateY: isEven ? 5 : -5 }}
                      transition={{ duration: 1.5, ease: "easeOut" }}
                      className="relative w-full aspect-[16/10] overflow-hidden"
                      style={{
                        maskImage: 'radial-gradient(circle at center, black 45%, transparent 90%)',
                        WebkitMaskImage: 'radial-gradient(circle at center, black 45%, transparent 90%)'
                      }}
                    >
                      <Image
                        src={pillar.image}
                        alt={pillar.title}
                        fill
                        className="object-cover brightness-100 contrast-100 transition-all duration-1000 group-hover:scale-110"
                      />
                      <div className="absolute inset-0 shadow-[inset_0_0_80px_rgba(0,0,0,0.05)] pointer-events-none" />
                    </motion.div>
                    <div className={`absolute -inset-10 bg-primary/[0.05] blur-[80px] rounded-full -z-10 transition-opacity duration-1000 ${isEven ? 'translate-x-10' : '-translate-x-10'}`} />
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
