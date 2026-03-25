import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css'; // Global styles
import SmoothScroll from '@/components/SmoothScroll';
import Chatbot from '@/components/Chatbot';

const inter = Inter({
  subsets: ['latin', 'vietnamese'],
  variable: '--font-sans',
});

export const metadata: Metadata = {
  title: 'Sàn Dịch Vụ - Hệ Sinh Thái Đa Tiện Ích 24/7',
  description: 'Kết nối 45+ ngành nghề dịch vụ từ Vận tải, Xây dựng, Điện lạnh đến Y tế và Làm đẹp ngay tại nhà.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${inter.variable}`}>
      <body className="font-sans bg-background-light text-slate-900 antialiased" suppressHydrationWarning>
        <SmoothScroll>
          {children}
        </SmoothScroll>
        <Chatbot />
      </body>
    </html>
  );
}
