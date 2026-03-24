'use client';

import { LayoutGrid, Facebook, Instagram, Youtube } from 'lucide-react';
import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="relative z-10 bg-surface pt-32 pb-16">
      <div className="max-w-[1740px] mx-auto px-4 md:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-12 gap-12 lg:gap-8 mb-24">
          <div className="col-span-2 lg:col-span-5 pr-0 lg:pr-20">
            <Link href="/" className="flex items-center gap-2 mb-8 group">
              <div className="size-9 bg-slate-900 rounded-xl flex items-center justify-center text-white group-hover:bg-primary transition-all duration-300">
                <LayoutGrid size={20} />
              </div>
              <span className="text-[20px] font-black tracking-tight text-slate-900 uppercase">Sàn Dịch Vụ</span>
            </Link>
            <p className="text-slate-500 text-[15px] max-w-sm leading-relaxed mb-8 font-medium">
              Sàn Dịch Vụ - Hệ sinh thái đa tiện ích hàng đầu Việt Nam, cung cấp giải pháp toàn diện cho mọi nhu cầu cuộc sống của bạn và gia đình.
            </p>
            <div className="flex gap-4">
              {[Facebook, Instagram, Youtube].map((Icon, idx) => (
                <Link
                  key={idx}
                  href="#"
                  className="size-10 rounded-xl bg-white border border-slate-100 shadow-sm flex items-center justify-center text-slate-400 hover:text-primary hover:border-primary/20 hover:shadow-md transition-all duration-300"
                >
                  <Icon size={18} />
                </Link>
              ))}
            </div>
          </div>

          <div className="lg:col-span-2">
            <h5 className="text-[13px] font-bold text-slate-900 uppercase tracking-[0.15em] mb-8">Dịch vụ chính</h5>
            <ul className="space-y-4">
              {['Vận tải & Di chuyển', 'Xây dựng, nội thất và kỹ thuật', 'Giúp việc, Chăm sóc & Làm đẹp', 'Y tế & Giáo dục', 'Du lịch, Khách sạn và Bảo hiểm'].map((item) => (
                <li key={item}>
                  <Link href="#" className="text-[14px] text-slate-500 font-medium hover:text-primary transition-colors">{item}</Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-2">
            <h5 className="text-[13px] font-bold text-slate-900 uppercase tracking-[0.15em] mb-8">Về Sàn Dịch Vụ</h5>
            <ul className="space-y-4">
              {['Về chúng tôi', 'Tin tức', 'Tuyển dụng', 'Liên hệ'].map((item) => (
                <li key={item}>
                  <Link href="#" className="text-[14px] text-slate-500 font-medium hover:text-primary transition-colors">{item}</Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-3">
            <h5 className="text-[13px] font-bold text-slate-900 uppercase tracking-[0.15em] mb-8">Hỗ trợ</h5>
            <ul className="space-y-4">
              {['Trung tâm trợ giúp', 'Điều khoản dịch vụ', 'Chính sách bảo mật', 'Câu hỏi thường gặp'].map((item) => (
                <li key={item}>
                  <Link href="#" className="text-[14px] text-slate-500 font-medium hover:text-primary transition-colors">{item}</Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="pt-12 border-t border-slate-200/60 flex flex-col md:flex-row justify-between items-center gap-6">
          <p className="text-[13px] text-slate-400 font-medium">
            © 2026 Sàn Dịch Vụ. Thangnq.
          </p>
        </div>
      </div>
    </footer>
  );
}
