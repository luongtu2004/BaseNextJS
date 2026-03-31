'use client';

import { motion } from 'motion/react';
import { MapPin, Phone, Mail, Clock, Send, Play } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';

export default function ContactPage() {
  return (
    <main className="min-h-screen bg-surface">
      {/* ─── Hero Section ─── */}
      <section className="relative pt-32 pb-20 overflow-hidden bg-primary text-white">
        <div className="absolute inset-0 z-0">
          <Image
            src="https://images.unsplash.com/photo-1497366216548-37526070297c?q=80&w=2069&auto=format&fit=crop"
            alt="Contact Office"
            fill
            className="object-cover opacity-20"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-primary via-primary/80 to-transparent" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 md:px-12 text-center mt-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <span className="px-4 py-1.5 rounded-full bg-white/20 backdrop-blur-md border border-white/20 text-[12px] font-black tracking-widest uppercase mb-6 inline-block">
              Hỗ trợ 24/7
            </span>
            <h1 className="text-[40px] md:text-[60px] font-black tracking-tight leading-[1.1] mb-6">
              Liên Hệ Với Chúng Tôi
            </h1>
            <p className="text-[18px] md:text-[20px] font-medium text-white/80 max-w-2xl mx-auto leading-relaxed">
              Sàn Dịch Vụ luôn sẵn sàng ở đây để lắng nghe và đồng hành cùng bạn giải quyết mọi vấn đề.
            </p>
          </motion.div>
        </div>
      </section>

      {/* ─── Contact Info Cards & Form ─── */}
      <section className="py-20 relative z-20 -mt-10">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left: Info Cards */}
            <div className="lg:col-span-1 space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="bg-white p-8 rounded-[32px] shadow-xl shadow-black/5 hover:shadow-2xl hover:shadow-primary/10 transition-all border border-black/5"
              >
                <div className="size-14 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-6">
                  <MapPin size={28} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Trụ Sở Chính</h3>
                <p className="text-[#5d4037] mb-1">Tầng 12, Tòa nhà Sàn Dịch Vụ Center,</p>
                <p className="text-[#5d4037]">Số 1 Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM</p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="bg-white p-8 rounded-[32px] shadow-xl shadow-black/5 hover:shadow-2xl hover:shadow-primary/10 transition-all border border-black/5"
              >
                <div className="size-14 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-6">
                  <Phone size={28} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Hotline Hỗ Trợ</h3>
                <p className="text-2xl font-black text-primary mb-2">1900 6868</p>
                <p className="text-[#5d4037] text-sm flex items-center gap-2">
                  <Clock size={16} /> Hoạt động 24/7 (Miễn phí cước)
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
                className="bg-white p-8 rounded-[32px] shadow-xl shadow-black/5 hover:shadow-2xl hover:shadow-primary/10 transition-all border border-black/5"
              >
                <div className="size-14 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-6">
                  <Mail size={28} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Email Đào Tạo & CSKH</h3>
                <p className="text-[#5d4037] font-medium hover:text-primary transition-colors cursor-pointer">
                  support@sandichvu.vn
                </p>
                <p className="text-[#5d4037] font-medium hover:text-primary transition-colors cursor-pointer mt-1">
                  partnership@sandichvu.vn
                </p>
              </motion.div>
            </div>

            {/* Right: Glassmorphism Form */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8 }}
              className="lg:col-span-2 bg-white rounded-[40px] p-8 md:p-12 shadow-2xl shadow-black/5 border border-black/5 relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 p-32 bg-primary/5 blur-[100px] rounded-full pointer-events-none" />
              <div className="absolute bottom-0 left-0 p-32 bg-blue-500/5 blur-[100px] rounded-full pointer-events-none" />

              <h2 className="text-[32px] font-black text-primary uppercase mb-2 relative z-10">Gửi Tin Nhắn Cho Chúng Tôi</h2>
              <p className="text-[#5d4037] font-medium mb-10 relative z-10">
                Hãy để lại lời nhắn, đội ngũ chuyên viên chăm sóc của Sàn Dịch Vụ sẽ phản hồi bạn sớm nhất có thể.
              </p>

              <form className="space-y-6 relative z-10" onSubmit={(e) => e.preventDefault()}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-slate-900 ml-2">Họ & Tên <span className="text-red-500">*</span></label>
                    <input
                      type="text"
                      className="w-full bg-slate-50 border-none rounded-2xl px-6 py-4 outline-none focus:ring-2 focus:ring-primary/20 focus:bg-white transition-all text-slate-900 placeholder:text-slate-400"
                      placeholder="Nguyễn Văn A"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-slate-900 ml-2">Số điện thoại <span className="text-red-500">*</span></label>
                    <input
                      type="tel"
                      className="w-full bg-slate-50 border-none rounded-2xl px-6 py-4 outline-none focus:ring-2 focus:ring-primary/20 focus:bg-white transition-all text-slate-900 placeholder:text-slate-400"
                      placeholder="0912 345 678"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-bold text-slate-900 ml-2">Chủ đề cần hỗ trợ</label>
                  <select className="w-full bg-slate-50 border-none rounded-2xl px-6 py-4 outline-none focus:ring-2 focus:ring-primary/20 focus:bg-white transition-all text-slate-900 appearance-none cursor-pointer">
                    <option value="">Chọn chủ đề...</option>
                    <option value="dich-vu">Hỗ trợ sử dụng dịch vụ</option>
                    <option value="doi-tac">Đăng ký đối tác/nhà cung cấp</option>
                    <option value="khieu-nai">Góp ý, khiếu nại chất lượng</option>
                    <option value="khac">Vấn đề khác</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-bold text-slate-900 ml-2">Nội dung chi tiết <span className="text-red-500">*</span></label>
                  <textarea
                    rows={5}
                    className="w-full bg-slate-50 border-none rounded-2xl px-6 py-4 outline-none focus:ring-2 focus:ring-primary/20 focus:bg-white transition-all text-slate-900 placeholder:text-slate-400 resize-none custom-scrollbar"
                    placeholder="Bạn cần chúng tôi hỗ trợ gì thêm?"
                  />
                </div>

                <motion.button
                  whileHover={{ scale: 1.02, backgroundColor: "#00a049" }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full bg-primary text-white font-bold text-lg py-5 rounded-2xl shadow-xl shadow-primary/20 flex items-center justify-center gap-2 transition-all"
                >
                  <Send size={20} />
                  GỬI YÊU CẦU
                </motion.button>
              </form>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─── Map Section ─── */}
      <section className="h-[500px] w-full bg-slate-200 relative overflow-hidden isolate shadow-inner group">
        <iframe
          src="https://maps.google.com/maps?q=Nguyen%20Hue%20Walking%20Street,%20Ho%20Chi%20Minh&t=&z=15&ie=UTF8&iwloc=&output=embed"
          className="absolute inset-0 w-full h-full border-0 transform-gpu grayscale-[0.2] contrast-[1.1] opacity-90 transition-opacity duration-700 pointer-events-none group-focus-within:pointer-events-auto group-active:pointer-events-auto"
          allowFullScreen={false}
          loading="lazy"
          title="Sàn Dịch Vụ Office Map"
          referrerPolicy="no-referrer-when-downgrade"
          style={{ 
            willChange: 'transform, opacity',
            backfaceVisibility: 'hidden',
          }}
        />
        
        {/* Anti-Scrollover Overlay: Blocks interaction until focused/clicked */}
        {/* When the user clicks, the focus-within pseudo-class enables the iframe interactions */}
        <div 
          className="absolute inset-0 z-10 transition-all duration-500 bg-white/5 backdrop-blur-[1px] group-focus-within:opacity-0 group-focus-within:pointer-events-none group-active:opacity-0 group-active:pointer-events-none flex flex-col items-center justify-center cursor-pointer"
          tabIndex={0}
        >
          <div className="px-6 py-3 bg-white/90 backdrop-blur-md rounded-full shadow-2xl border border-black/5 text-primary text-sm font-black flex items-center gap-3 active:scale-95 transition-transform">
             <div className="size-2 bg-emerald-500 rounded-full animate-pulse" />
             NHẤN ĐỂ TƯƠNG TÁC VỚI BẢN ĐỒ
          </div>
        </div>

        {/* Shadow Overlay */}
        <div className="absolute inset-0 z-20 pointer-events-none shadow-[inset_0_20px_60px_rgba(0,0,0,0.1)]" />
      </section>

    </main>
  );
}
