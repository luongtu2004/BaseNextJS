import type { Metadata } from 'next';
import Link from 'next/link';
import { LayoutGrid } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Xác thực - Sàn Dịch Vụ',
  description: 'Đăng nhập và đăng ký tài khoản Sàn Dịch Vụ',
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white flex flex-col relative overflow-hidden selection:bg-emerald-500/30 selection:text-emerald-900">
      {/* High-Fidelity Bright Gradient Background (Light Green & Beige/Brown) */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden bg-white">
        <div 
          className="absolute inset-0 opacity-[1]"
          style={{ 
            background: `linear-gradient(135deg, #f0f9f1 0%, #ffffff 50%, #f9f7f4 100%)` 
          }} 
        />
        <div className="absolute top-[-5%] left-[-5%] w-[50%] h-[50%] rounded-full bg-emerald-100/40 blur-[100px] animate-pulse" />
        <div className="absolute bottom-[-5%] right-[-5%] w-[50%] h-[50%] rounded-full bg-orange-50/40 blur-[100px]" />
        
        {/* Anti-Gravity Grain */}
        <div className="absolute inset-0 opacity-[0.02] mix-blend-multiply pointer-events-none" style={{ backgroundImage: 'url("https://www.transparenttextures.com/patterns/felt.png")' }} />
      </div>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-6 relative z-10">
        <div className="w-full max-w-[460px] bg-white/70 backdrop-blur-[48px] rounded-[48px] shadow-[0_32px_80px_-20px_rgba(0,0,0,0.12)] p-10 md:p-12 border border-white/40 ring-1 ring-black/5 relative overflow-hidden">
          {/* Top accent line */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-1.5 bg-black/5 rounded-b-full px-1" />

          {children}
        </div>
      </main>
    </div>
  );
}
