'use client';

import { ChevronRight, Rocket, Home, HeartHandshake, Stethoscope, Plane } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { PILLARS } from '@/lib/constants';
import { createSlug } from '@/lib/utils';
import { motion, useScroll, useTransform } from 'motion/react';
import { useRef, useState } from 'react';
import TypingText from './TypingText';

const iconMap: Record<string, any> = {
  transportation: Rocket,
  construction_electronics: Home,
  housekeeping_beauty: HeartHandshake,
  education: Stethoscope,
  travel: Plane,
};

export default function CoreServices() {
  const [headerStep, setHeaderStep] = useState(0);
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  // Zoom-up effect: Scales from 0.8 to 1.1 and back down/up
  // We want it to be "zoom to trồi lên" so it should reach 1.0 when in center
  const scale = useTransform(scrollYProgress, [0, 0.4, 0.6, 1], [0.85, 1, 1, 0.85]);
  const y = useTransform(scrollYProgress, [0, 0.4, 0.6, 1], [100, 0, 0, -100]);
  const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);

  return (
    <section id="services" ref={containerRef} className="py-20 bg-surface overflow-hidden">
      <div className="max-w-[1740px] mx-auto px-4 md:px-8">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-x-12 gap-y-6 mb-32 border-b border-slate-900/10 pb-12">
          <div className="flex flex-col md:flex-row md:items-center gap-x-8 gap-y-2">
            <motion.span
              className="text-slate-900 font-bold tracking-[0.2em] uppercase text-[20px]"
            >
              <TypingText 
                text="Hệ sinh thái chính" 
                delay={0.1} 
                showCursor={false} 
                onComplete={() => setHeaderStep(1)}
              />
            </motion.span>
            <div className="hidden md:block w-px h-6 bg-slate-900/20" />
            <h2 className="text-[20px] font-black text-slate-900 tracking-tight uppercase">
              <TypingText 
                text={`${PILLARS.length} Trụ Cột Dịch Vụ`}
                delay={0.2} 
                showCursor={false} 
                start={headerStep >= 1}
                onComplete={() => setHeaderStep(2)}
              />
            </h2>
          </div>
          <div className="max-w-xl">
            <p className="text-[20px] text-slate-900 font-medium leading-snug">
              Sự hội tụ của 45 ngành nghề dịch vụ chuyên nghiệp, đáp ứng mọi khía cạnh trong cuộc sống của bạn.
            </p>
          </div>
        </div>

        <div className="space-y-8">
          {PILLARS.map((pillar, index) => {
            const Icon = iconMap[pillar.id] || Rocket;
            const isEven = index % 2 === 0;

            return (
              <motion.div
                key={pillar.id}
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8 }}
                className="flex flex-col lg:flex-row lg:items-center gap-12 lg:gap-24"
              >
                {/* Text Content Column */}
                <div className="flex-1 space-y-6">
                  <div className="flex items-center gap-4">
                    <span className="text-[14px] font-black text-primary/40 uppercase tracking-widest">
                      {index + 1 < 10 ? `0${index + 1}` : index + 1}
                    </span>
                    <div className="h-[1px] w-12 bg-primary/20" />
                  </div>

                  <div>
                    <h3 className="text-[32px] md:text-[44px] font-black mb-4 text-slate-900 tracking-tight leading-none uppercase">
                      {pillar.title}
                    </h3>
                    <p className="text-[18px] md:text-[20px] text-slate-500 font-medium leading-relaxed max-w-xl">
                      {pillar.description}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 max-w-2xl">
                    {pillar.industries.slice(0, 8).map((ind, idx) => (
                      <div key={idx} className="flex items-start gap-3 text-[15px] text-slate-600 font-medium group/item hover:text-primary transition-colors">
                        <div className="mt-2 w-1 h-1 rounded-full bg-slate-200 group-hover/item:bg-primary transition-colors shrink-0" />
                        <span className="leading-tight">{ind}</span>
                      </div>
                    ))}
                    {pillar.industries.length > 8 && (
                      <div className="text-[12px] font-bold text-slate-300 uppercase tracking-wide pt-1">
                        + {pillar.industries.length - 8} dịch vụ khác
                      </div>
                    )}
                  </div>

                  <Link
                    href={`/danh-muc/${createSlug(pillar.title)}`}
                    className="inline-flex items-center gap-3 text-[16px] font-bold text-slate-900 group/btn hover:text-primary transition-all pt-4"
                  >
                    <div className="size-10 rounded-full bg-slate-100 flex items-center justify-center group-hover/btn:bg-primary group-hover/btn:text-white transition-all duration-300">
                      <ChevronRight size={20} />
                    </div>
                    Xem chi tiết dịch vụ
                  </Link>
                </div>

                {/* Image Column */}
                <div className="flex-1 relative group">
                  <div className="relative aspect-[4/3] rounded-[48px] overflow-hidden apple-card-shadow group-hover:apple-card-shadow-hover transition-all duration-700 bg-white border border-slate-100">
                    <Image
                      src={pillar.image}
                      alt={pillar.title}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform duration-1000 ease-out"
                    />
                    {/* Subtle overlay gradient */}
                    <div className="absolute inset-0 bg-gradient-to-tr from-black/5 to-transparent pointer-events-none" />
                  </div>

                  {/* Floating Icon Decoration */}
                  <motion.div
                    animate={{ y: [0, -10, 0] }}
                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute -top-6 -right-6 size-20 rounded-3xl bg-white shadow-2xl flex items-center justify-center text-primary border border-slate-50 z-20"
                  >
                    <Icon size={32} />
                  </motion.div>

                  {/* Aesthetic Background Glow */}
                  <div className={`absolute -inset-4 bg-primary/5 blur-[80px] rounded-full -z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-700`} />
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
