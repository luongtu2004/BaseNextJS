'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchAPI } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { useAuth } from '@/contexts/AuthContext';
import { Phone, Lock, Loader2, ArrowRight } from 'lucide-react';

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
    <>
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>Đăng nhập</h1>
        <p className="text-slate-500 text-sm" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>Chào mừng bạn trở lại hệ thống</p>
      </div>

      <form onSubmit={handleLogin} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 text-red-600 text-sm rounded-xl border border-red-100">
            {error}
          </div>
        )}

        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>Số điện thoại</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Phone size={18} className="text-slate-400" />
            </div>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#1a6b51]/20 focus:border-[#1a6b51] outline-none transition-all text-sm"
              placeholder="0912 345 678"
              required
              style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
            />
          </div>
        </div>

        <div className="space-y-1.5 pt-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-slate-700" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>Mật khẩu</label>
            <Link href="#" className="text-xs font-medium text-[#1a6b51] hover:text-[#00523b] transition-colors" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
              Quên mật khẩu?
            </Link>
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock size={18} className="text-slate-400" />
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#1a6b51]/20 focus:border-[#1a6b51] outline-none transition-all text-sm"
              placeholder="••••••••"
              required
              style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-6 bg-gradient-to-r from-[#1a6b51] to-[#00523b] hover:from-[#00523b] hover:to-[#1a6b51] text-white font-semibold py-3 px-4 rounded-xl shadow-lg ring-1 ring-black/10 transition-all flex items-center justify-center gap-2 group disabled:opacity-70"
          style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
        >
          {loading ? (
            <Loader2 size={20} className="animate-spin" />
          ) : (
            <>
              Đăng nhập ngay
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </>
          )}
        </button>
      </form>

      <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-center gap-1.5 text-sm">
        <span className="text-slate-500" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>Chưa có tài khoản?</span>
        <Link href="/register" className="font-semibold text-[#1a6b51] hover:text-[#00523b] transition-colors" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
          Đăng ký ngay
        </Link>
      </div>
    </>
  );
}
