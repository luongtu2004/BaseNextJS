'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchAPI } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { useAuth } from '@/contexts/AuthContext';
import { Phone, Lock, Loader2, ArrowRight } from 'lucide-react';
import { motion } from 'motion/react';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // 1. Gửi request login
      const res = await fetchAPI<{ access_token: string; refresh_token: string }>('/api/v1/auth/login/password', {
        method: 'POST',
        body: JSON.stringify({ phone, password }),
      });

      // 2. Lưu token
      if (res && res.access_token) {
        await login(res.access_token);

        // Redirect
        const session = await getSession();
        if (session && session.roles.includes('admin')) {
          router.replace('/admin');
        } else {
          router.replace('/');
        }
      }
    } catch (err: any) {
      setError(err.message || 'Số điện thoại hoặc mật khẩu không chính xác.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="text-center mb-10">
        <h1 className="text-3xl md:text-4xl font-black text-slate-900 mb-3 tracking-tight uppercase" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
          Đăng nhập
        </h1>
        <p className="text-slate-500 text-[15px] font-medium" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
          Chào mừng bạn trở lại hệ sinh thái Sàn Dịch Vụ
        </p>
      </div>

      <form onSubmit={handleLogin} className="space-y-6">
        {error && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-4 bg-red-50 text-red-600 text-sm font-bold rounded-[20px] border border-red-100 flex items-center gap-3"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
            {error}
          </motion.div>
        )}

        <div className="space-y-2">
          <label className="text-[13px] font-black text-slate-400 uppercase tracking-widest ml-1" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
            Số điện thoại
          </label>
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-emerald-500 transition-colors">
              <Phone size={20} strokeWidth={2.5} />
            </div>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full pl-12 pr-4 py-4 bg-black/[0.03] border border-black/5 rounded-[24px] focus:bg-white focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 outline-none transition-all text-base font-bold placeholder:text-slate-300"
              placeholder="0912 345 678"
              required
              style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
            />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between ml-1">
            <label className="text-[13px] font-black text-slate-400 uppercase tracking-widest" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
              Mật khẩu
            </label>
            <Link href="#" className="text-[12px] font-black text-emerald-600 hover:text-emerald-700 transition-colors uppercase tracking-tight" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
              Quên mật khẩu?
            </Link>
          </div>
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-emerald-500 transition-colors">
              <Lock size={20} strokeWidth={2.5} />
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-12 pr-4 py-4 bg-black/[0.03] border border-black/5 rounded-[24px] focus:bg-white focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 outline-none transition-all text-base font-bold placeholder:text-slate-300"
              placeholder="••••••••"
              required
              style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full pt-2 group"
          style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
        >
          <div className="w-full bg-slate-900 text-white font-black py-4 px-6 rounded-[24px] shadow-[0_20px_40px_-12px_rgba(0,0,0,0.2)] hover:shadow-[0_24px_48px_-12px_rgba(0,0,0,0.3)] hover:-translate-y-0.5 active:translate-y-0.5 transition-all flex items-center justify-center gap-3 relative overflow-hidden group-disabled:opacity-70 group-disabled:pointer-events-none">
            {/* Subtle gloss effect */}
            <div className="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent pointer-events-none" />
            
            {loading ? (
              <Loader2 size={24} className="animate-spin" />
            ) : (
              <>
                <span className="uppercase tracking-wider">Đăng nhập ngay</span>
                <ArrowRight size={20} strokeWidth={3} className="group-hover:translate-x-1.5 transition-transform" />
              </>
            )}
          </div>
        </button>
      </form>

      <div className="mt-12 pt-8 border-t border-black/5 flex flex-col items-center gap-4 text-center">
        <p className="text-slate-400 text-sm font-bold uppercase tracking-tight" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
          Chưa có tài khoản?
        </p>
        <Link 
          href="/register" 
          className="w-full py-4 border-2 border-slate-900/5 rounded-[24px] font-black text-slate-900 hover:bg-slate-50 transition-all uppercase tracking-wider text-sm"
          style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
        >
          Đăng ký tài khoản mới
        </Link>
      </div>
    </motion.div>
  );
}
