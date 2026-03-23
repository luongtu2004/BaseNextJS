'use client';

import { Apple, Play } from 'lucide-react';
import Image from 'next/image';
import { motion, useScroll, useTransform, useSpring } from 'motion/react';
import { useRef } from 'react';

export default function AppPromotion() {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  // Use spring to smooth out the jittery scroll values
  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });

  const scale = useTransform(smoothProgress, [0, 0.45, 0.55, 1], [0.8, 1, 1, 0.8]);
  const y = useTransform(smoothProgress, [0, 0.45, 0.55, 1], [100, 0, 0, -100]);
  const opacity = useTransform(smoothProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);

  return (
    <section ref={containerRef} className="pb-24 pt-0 bg-[#fbfbfd] overflow-hidden">
      <div className="max-w-[1740px] mx-auto px-4 md:px-8">
        <motion.div 
          style={{ scale, y, opacity }}
          className="bg-slate-900 rounded-[48px] overflow-hidden relative"
        >
          <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-20 p-12 md:p-20 relative z-10">
            <div className="flex-1 text-left">
              <motion.span 
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 0.6 }}
                className="text-white font-bold tracking-[0.2em] uppercase text-[12px] mb-6 block"
              >
                Trải nghiệm di động
              </motion.span>
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-white mb-8 leading-[1.1] tracking-tight">
                Mọi dịch vụ <br /> 
                <span className="text-white">trong lòng bàn tay</span>
              </h2>
              <p className="text-lg md:text-xl text-slate-400 mb-12 leading-relaxed max-w-lg font-medium">
                Tải ứng dụng Sàn Dịch Vụ ngay để tận hưởng sự tiện nghi, theo dõi tiến độ công việc và nhận hàng ngàn ưu đãi hấp dẫn.
              </p>
              
              <div className="flex flex-wrap gap-5">
                <motion.button 
                  whileHover={{ scale: 1.05, y: -5 }}
                  whileTap={{ scale: 0.95 }}
                  className="bg-white text-slate-900 px-8 py-4 rounded-2xl flex items-center gap-3 transition-all cursor-pointer shadow-lg"
                >
                  <Apple size={28} className="fill-current" />
                  <div className="text-left">
                    <p className="text-[10px] uppercase font-black leading-none opacity-40">Download on</p>
                    <p className="text-[17px] font-extrabold leading-none mt-1">App Store</p>
                  </div>
                </motion.button>
                <motion.button 
                  whileHover={{ scale: 1.05, y: -5 }}
                  whileTap={{ scale: 0.95 }}
                  className="bg-slate-800 text-white px-8 py-4 rounded-2xl flex items-center gap-3 transition-all border border-slate-700 cursor-pointer shadow-lg"
                >
                  <Play size={28} className="fill-current" />
                  <div className="text-left">
                    <p className="text-[10px] uppercase font-black leading-none opacity-40">Get it on</p>
                    <p className="text-[17px] font-extrabold leading-none mt-1">Google Play</p>
                  </div>
                </motion.button>
              </div>
            </div>

            <div className="flex-1 relative">
              <motion.div 
                initial={{ rotate: 5, y: 50 }}
                whileInView={{ rotate: 0, y: 0 }}
                transition={{ duration: 1 }}
                className="relative z-10"
              >
                <div className="relative mx-auto w-[280px] md:w-[320px] aspect-[1/2]">
                  <Image 
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuCrcTQKUxXCb3HQLSF6yQM54aekvI2DW68XW-oaYVDtzuxcPcCQzRuZz0FCaDttkXZwdjBSx45jrgQr82xyJTKsXPxJvFC0T3vahnCLvtzhW5fFvFd1rf4MRLOXSQDN_azejaQxp7x29zmPezrv6tSmcuX-0OkEBxlw2IqrNkj5-q7yLKIhAVYUDb2STKfHv9XPh44KmLOzzAuQuLt3FqMQ098hmMShIWsyHp5PrcjUaXan9oPrzGDKLdfSeRz6wp71qqyLhnxBd_50" 
                    alt="App Preview" 
                    fill
                    className="rounded-[3rem] shadow-[0_50px_100px_rgba(0,0,0,0.5)] border-8 border-slate-800 object-cover"
                  />
                </div>
              </motion.div>
            </div>
          </div>

          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/20 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/2"></div>
          <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-slate-400/10 rounded-full blur-[120px] translate-y-1/2 -translate-x-1/2"></div>
        </motion.div>
      </div>
    </section>
  );
}