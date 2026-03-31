'use client';

import { LayoutGrid, Facebook, Instagram, Youtube } from 'lucide-react';
import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="relative z-10 bg-white pt-32 pb-16 border-t border-black/5">
      <div className="max-w-[1740px] mx-auto px-6 md:px-12">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-12 gap-12 lg:gap-8 mb-24">
          <div className="col-span-2 lg:col-span-5 pr-0 lg:pr-24">
            <Link href="/" className="flex items-center gap-3 mb-10 group">
              <div className="size-11 bg-primary rounded-2xl flex items-center justify-center text-white group-hover:scale-105 transition-all duration-500 shadow-lg shadow-primary/20">
                <LayoutGrid size={24} />
              </div>
              <span className="text-[24px] font-black tracking-tighter text-primary uppercase">Sàn Dịch Vụ</span>
            </Link>
            <p className="text-[#5d4037] text-[16px] max-w-sm leading-relaxed mb-10 font-bold opacity-70 uppercase tracking-tight">
              Hệ sinh thái đa tiện ích hàng đầu Việt Nam, cung cấp giải pháp toàn diện cho mọi nhu cầu cuộc sống của bạn và gia đình.
            </p>
            <div className="flex gap-5">
              {[Facebook, Instagram, Youtube].map((Icon, idx) => (
                <Link
                  key={idx}
                  href="#"
                  className="size-12 rounded-2xl bg-white border border-black/5 shadow-sm flex items-center justify-center text-[#5d4037] hover:text-white hover:bg-primary hover:border-primary transition-all duration-500"
                >
                  <Icon size={20} />
                </Link>
              ))}
            </div>
          </div>

          <div className="lg:col-span-2">
            <h5 className="text-[13px] font-black text-primary uppercase tracking-[0.2em] mb-10 opacity-60">Dịch vụ chính</h5>
            <ul className="space-y-5">
              {['Vận tải & Di chuyển', 'Xây dựng & Kỹ thuật', 'Giúp việc & Làm đẹp', 'Y tế & Giáo dục', 'Du lịch & Bảo hiểm'].map((item) => (
                <li key={item}>
                  <Link href="#" className="text-[15px] text-[#5d4037] font-bold hover:text-primary transition-all duration-300 opacity-80 hover:opacity-100">{item}</Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-2">
            <h5 className="text-[13px] font-black text-primary uppercase tracking-[0.2em] mb-10 opacity-60">Về chúng tôi</h5>
            <ul className="space-y-5">
              {['Câu chuyện thương hiệu', 'Tin tức & Sự kiện', 'Cơ hội nghề nghiệp', 'Liên hệ hợp tác'].map((item) => (
                <li key={item}>
                  <Link href="#" className="text-[15px] text-[#5d4037] font-bold hover:text-primary transition-all duration-300 opacity-80 hover:opacity-100">{item}</Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-3">
            <h5 className="text-[13px] font-black text-primary uppercase tracking-[0.2em] mb-10 opacity-60">Hỗ trợ khách hàng</h5>
            <ul className="space-y-5">
              {['Trung tâm trợ giúp', 'Điều khoản sử dụng', 'Chính sách bảo mật', 'Câu hỏi thường gặp'].map((item) => (
                <li key={item}>
                  <Link href="#" className="text-[15px] text-[#5d4037] font-bold hover:text-primary transition-all duration-300 opacity-80 hover:opacity-100">{item}</Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="pt-12 border-t border-black/5 flex flex-col md:flex-row justify-between items-center gap-6">
          <p className="text-[14px] text-[#5d4037] font-bold opacity-40 uppercase tracking-widest">
            © 2026 Sàn Dịch Vụ. THANGNQ. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
