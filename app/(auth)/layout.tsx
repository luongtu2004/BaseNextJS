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
      {/* High-Fidelity iOS 26 Mesh Gradient Background */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[70%] rounded-full bg-emerald-400/15 blur-[120px] animate-pulse" style={{ animationDuration: '8s' }} />
        <div className="absolute bottom-[-20%] right-[-10%] w-[80%] h-[80%] rounded-full bg-indigo-500/15 blur-[140px] animate-pulse" style={{ animationDuration: '12s' }} />
        <div className="absolute top-[20%] right-[10%] w-[40%] h-[40%] rounded-full bg-blue-400/10 blur-[100px]" />

        {/* Anti-Gravity Particles (Subtle) */}
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(0,0,0,0.05) 1px, transparent 0)', backgroundSize: '40px 40px' }} />
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
