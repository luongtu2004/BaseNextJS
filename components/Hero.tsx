'use client';

import { motion, useScroll, useTransform } from 'motion/react';
import { useRef, useState } from 'react';
import ParticleBackground from './ParticleBackground';
import TypingText from './TypingText';

export default function Hero() {
  const [typingStep, setTypingStep] = useState(0);
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  });

  // Smooth parallax
  const bgY = useTransform(scrollYProgress, [0, 1], [0, 150]);
  const contentY = useTransform(scrollYProgress, [0, 1], [0, 80]);
  const contentOpacity = useTransform(scrollYProgress, [0, 0.6], [1, 0]);

  return (
    <section
      ref={containerRef}
      className="relative w-full h-[100vh] overflow-hidden bg-surface flex items-center justify-center"
    >
      {/* ─── Background ─── */}
      <motion.div
        style={{ y: bgY }}
        className="absolute inset-0 z-0 bg-surface"
      />

      {/* ─── Particle Layer ─── */}
      <div className="absolute inset-0 z-[1] pointer-events-none opacity-25">
        <ParticleBackground />
      </div>

      {/* ─── Content ─── */}
      <motion.div
        style={{ y: contentY, opacity: contentOpacity }}
        className="relative z-10 w-full max-w-[1740px] mx-auto px-6 md:px-16"
      >
        <div className="grid grid-cols-1 lg:grid-cols-3 items-center gap-12 lg:gap-24 min-h-[75vh]">
          {/* Left Content Column */}
          <div className="text-left lg:col-span-2">
            {/* Tagline */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mb-8"
            >
              <div className="flex items-center gap-4">
                <div className="h-[2px] w-12 bg-primary" />
                <span className="text-primary font-bold tracking-[0.3em] uppercase text-[12px] md:text-[14px]">
                  Kết Nối Dịch Vụ - Vươn Tầm Việt Nam
                </span>
              </div>
            </motion.div>

            {/* Hero Heading — Increased line-height and spacing between lines */}
            <h1 className="text-[32px] md:text-[48px] lg:text-[60px] font-black leading-[1.15] tracking-[-0.04em] mb-10 uppercase text-slate-900">
              <span className="block mb-6">
                <TypingText
                  text="Giải Pháp Tận Tâm"
                  delay={0.4}
                  onComplete={() => setTypingStep(1)}
                />
              </span>
              <span className="block text-primary">
                <TypingText
                  text="Chất Lượng Vững Bền."
                  delay={0.1}
                  stagger={0.06}
                  start={typingStep >= 1}
                  onComplete={() => setTypingStep(2)}
                />
              </span>
            </h1>

            <motion.p
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 1.6 }}
              className="text-[17px] md:text-[21px] text-slate-500 font-medium max-w-xl mb-12 leading-[1.65] tracking-tight"
            >
              Hệ sinh thái kết nối chuyên gia hàng đầu, đồng hành cùng bạn giải quyết mọi nhu cầu cuộc sống một cách chuyên nghiệp, minh bạch và tin cậy nhất.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: typingStep >= 2 ? 0.2 : 2.2 }}
              className="flex flex-wrap items-center gap-6"
            >
              <motion.button
                whileHover={{ scale: 1.03, boxShadow: "0 15px 30px -8px rgba(0, 177, 79, 0.25)" }}
                whileTap={{ scale: 0.97 }}
                className="btn-primary-gradient px-12 py-5 rounded-[22px] text-[17px] font-bold cursor-pointer transition-all hover:brightness-105"
              >
                Trải nghiệm ngay
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.03, backgroundColor: "#f8fafc" }}
                whileTap={{ scale: 0.97 }}
                className="bg-surface-container-lowest text-on-surface px-12 py-5 rounded-[22px] text-[17px] font-bold ghost-border cursor-pointer"
              >
                Tìm hiểu thêm
              </motion.button>
            </motion.div>
          </div>

          {/* Right Visual Column — Vietnam Connectivity Map */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1.2, delay: 0.4 }}
            className="hidden lg:flex items-center justify-center relative min-h-[550px] hero-visual-container lg:col-span-1"
          >
            <div className="relative w-full h-full flex items-center justify-center">
              {/* Vietnam Connectivity Map (Generated Image) */}
              <motion.img
                src="/vietnam-map.png?v=3"
                alt="Vietnam Connectivity Map"
                className="w-full max-w-[500px] object-contain opacity-90 mix-blend-multiply"
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
              />
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Decorative bottom fade — Simplified */}
      <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-surface to-transparent z-20 pointer-events-none" />
    </section>
  );
}