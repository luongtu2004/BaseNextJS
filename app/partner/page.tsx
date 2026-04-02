'use client';

import { motion } from 'motion/react';
import { Target, ShieldCheck, TrendingUp, HandCoins, Users, Banknote, ArrowRight } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';

const benefits = [
  {
    icon: Users,
    title: 'Tiếp Cận Hàng Triệu Khách Hàng',
    description: 'Hệ thống Sàn Dịch Vụ giúp bạn kết nối với lượng lớn khách hàng sinh sống tại khu vực xung quanh mà không tốn chi phí Marketing.'
  },
  {
    icon: Banknote,
    title: 'Gia Tăng Thu Nhập',
    description: 'Nhận yêu cầu liên tục từ hệ thống. Bạn có quyền làm chủ thời gian, gia tăng thêm nguồn thu nhập bền vững không giới hạn.'
  },
  {
    icon: ShieldCheck,
    title: 'Thanh Toán Đảo Bảo',
    description: 'Mọi giao dịch đều được đảm bảo 100% qua nền tảng thanh toán thông minh của chúng tôi. Rút tiền nhanh chóng.'
  },
  {
    icon: TrendingUp,
    title: 'Đào Tạo Chuyên Sâu',
    description: 'Được tham gia các khóa huấn luyện kỹ năng, nâng cao tay nghề và tư duy chăm sóc khách hàng từ các chuyên gia hàng đầu.'
  }
];

export default function PartnerPage() {
  return (
    <main className="min-h-screen bg-slate-50">
      {/* ─── Hero Section ─── */}
      <section className="relative pt-32 pb-24 overflow-hidden bg-slate-900 border-b-8 border-primary">
        <div className="absolute inset-0 z-0">
          <Image
            src="https://images.unsplash.com/photo-1600880292203-757bb62b4baf?q=80&w=2070&auto=format&fit=crop"
            alt="Partnership"
            fill
            className="object-cover opacity-30 mix-blend-luminosity"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-slate-900 via-slate-900/80 to-transparent" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 md:px-12 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
          >
            <span className="px-4 py-1.5 rounded-full bg-primary/20 border border-primary/30 text-[12px] font-black tracking-widest uppercase mb-6 inline-block text-primary">
              Chương trình Đối Tác Vàng
            </span>
            <h1 className="text-[44px] md:text-[64px] font-black text-white tracking-tight leading-[1.1] mb-6 uppercase drop-shadow-lg">
              Trở Thành <br/><span className="text-primary">Đối Tác</span> Của Sàn Dịch Vụ
            </h1>
            <p className="text-[18px] md:text-[20px] font-medium text-white/80 max-w-lg leading-relaxed mb-10">
              Gia nhập hệ sinh thái lớn nhất Việt Nam, kết nối hàng triệu khách hàng và bứt phá doanh thu.
            </p>
            <Link href="/contact">
              <motion.button
                whileHover={{ scale: 1.05, boxShadow: "0 20px 40px -10px rgba(0, 177, 79, 0.4)" }}
                whileTap={{ scale: 0.95 }}
                className="bg-primary hover:bg-[#00a049] text-white px-10 py-5 rounded-[22px] font-black text-[18px] shadow-xl transition-all cursor-pointer inline-flex items-center gap-3"
              >
                ĐĂNG KÝ NGAY <Target size={22} />
              </motion.button>
            </Link>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="hidden lg:block relative"
          >
            <div className="w-full max-w-md ml-auto aspect-square bg-white/5 backdrop-blur-3xl rounded-[40px] border border-white/10 p-8 shadow-2xl skew-y-6 rotate-3">
              <div className="grid grid-cols-2 gap-4 h-full">
                <div className="bg-primary/20 rounded-2xl" />
                <div className="bg-white/10 rounded-2xl" />
                <div className="bg-white/10 rounded-2xl" />
                <div className="bg-primary/80 rounded-2xl flex items-center justify-center">
                  <HandCoins size={64} className="text-white drop-shadow-md" />
                </div>
              </div>
            </div>
            <div className="absolute top-1/2 -left-12 -translate-y-1/2 p-6 bg-white rounded-3xl shadow-2xl shadow-primary/20 z-10 animate-bounce cursor-default border border-black/5">
              <div className="text-[32px] font-black text-slate-900">+50K</div>
              <div className="text-[14px] font-bold text-slate-400 uppercase tracking-wide">Yêu cầu mỗi tháng</div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ─── Benefits Section ─── */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-[36px] md:text-[48px] font-black text-primary tracking-[-0.04em] leading-tight uppercase mb-6">
              Tại sao nên hợp tác?
            </h2>
            <p className="text-[18px] font-medium text-[#5d4037] opacity-80">
              Sàn Dịch Vụ cung cấp hạ tầng công nghệ giúp bạn tự do tài chính mà không cần bỏ chi phí vận hành.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
            {benefits.map((benefit, idx) => (
              <motion.div 
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                className="bg-white p-10 rounded-[40px] shadow-[0_10px_40px_rgba(0,0,0,0.03)] border border-black/[0.03] hover:shadow-[0_20px_60px_rgba(0,0,0,0.08)] hover:border-primary/20 transition-all group"
              >
                <div className="flex flex-col sm:flex-row gap-8 items-start">
                  <div className="size-20 shrink-0 bg-primary/5 rounded-[24px] flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-white group-hover:scale-110 transition-all duration-500 shadow-sm border border-primary/10">
                    <benefit.icon size={36} strokeWidth={2.5} />
                  </div>
                  <div>
                    <h3 className="text-[22px] font-black text-slate-900 mb-3 group-hover:text-primary transition-colors">{benefit.title}</h3>
                    <p className="text-[16px] text-[#5d4037] leading-relaxed opacity-80">{benefit.description}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Application Form CTA ─── */}
      <section className="pb-32">
        <div className="max-w-5xl mx-auto px-6 md:px-12">
          <div className="bg-primary rounded-[48px] p-10 md:p-16 lg:p-20 text-center relative overflow-hidden shadow-2xl shadow-primary/30 origin-bottom border border-black/5 hover:scale-[1.01] transition-transform duration-700">
            <div className="absolute top-0 right-0 p-32 bg-white/10 blur-[100px] rounded-full" />
            <div className="absolute bottom-0 left-0 p-32 bg-black/10 blur-[100px] rounded-full" />
            
            <h2 className="text-[32px] md:text-[48px] font-black text-white leading-tight mb-6 relative z-10">
              SẴN SÀNG TRỞ THÀNH<br/>ĐỐI TÁC CHƯA?
            </h2>
            <p className="text-[18px] text-white/90 mb-10 max-w-2xl mx-auto font-medium relative z-10">
              Chỉ với 3 bước đơn giản: Tải ứng dụng, Điền hồ sơ và Đợi kiểm duyệt. Bạn đã sẵn sàng để đón nhận những khách hàng đầu tiên.
            </p>
            <div className="flex flex-col sm:flex-row justify-center items-center gap-6 relative z-10">
              <Link href="/contact" className="w-full sm:w-auto">
                <button className="bg-white text-primary px-10 py-5 rounded-2xl font-black text-[18px] w-full hover:bg-slate-50 shadow-xl flex items-center justify-center gap-2 group transition-all">
                  ĐĂNG KÝ TƯ VẤN
                  <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                </button>
              </Link>
              <Link href="/" className="w-full sm:w-auto">
                <button className="bg-transparent text-white px-10 py-5 rounded-2xl font-black text-[18px] w-full border-2 border-white/30 hover:bg-white/10 transition-all flex items-center justify-center">
                  TẢI ỨNG DỤNG NGAY
                </button>
              </Link>
            </div>
          </div>
        </div>
      </section>

    </main>
  );
}
