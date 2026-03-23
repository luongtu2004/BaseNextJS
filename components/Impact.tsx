'use client';

import { motion, useScroll, useTransform } from 'motion/react';
import { useRef } from 'react';

const stats = [
  { value: '100%', label: 'Hài lòng khách hàng' },
  { value: '2.5M+', label: 'Khách hàng tin dùng' },
  { value: '15K+', label: 'Chuyên gia đối tác' },
  { value: '1M+', label: 'Dịch vụ hoàn chỉnh' },
];

export default function Impact() {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  const scale = useTransform(scrollYProgress, [0, 0.4, 0.6, 1], [0.8, 1, 1, 0.8]);
  const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);

  return (
    <section ref={containerRef} className="py-24 bg-white overflow-hidden">
      <div className="max-w-[1740px] mx-auto px-4 md:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 md:gap-16">
          {stats.map((stat, index) => (
            <motion.div 
              key={index}
              className="group text-center"
            >
              <div className="mb-4 inline-block">
                <span className="text-[44px] md:text-[56px] font-black text-slate-900 tracking-tighter leading-none block group-hover:text-primary transition-colors duration-500">
                  {stat.value}
                </span>
                <div className="h-[2px] w-0 group-hover:w-full bg-primary transition-all duration-500 mx-auto mt-1" />
              </div>
              <p className="text-[13px] md:text-[15px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-2">
                {stat.label}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
