'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchAPI, setToken } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { Phone, Lock, User, KeyRound, Loader2, ArrowRight, ArrowLeft } from 'lucide-react';

export default function RegisterPage() {
  const router = useRouter();
  
  // Step 1 states
  const [step, setStep] = useState<1 | 2>(1);
  const [phone, setPhone] = useState('');
  const [otpSessionId, setOtpSessionId] = useState('');
  
  // Step 2 states
  const [otpCode, setOtpCode] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  
  // Common states
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone) return;
    
    setError('');
    setLoading(true);

    try {
      const res = await fetchAPI<{ otp_session_id: string; expired_in: number }>('/api/v1/auth/otp/send', {
        method: 'POST',
        body: JSON.stringify({ phone }),
      });

      if (res && res.otp_session_id) {
        setOtpSessionId(res.otp_session_id);
        setStep(2);
      }
    } catch (err: any) {
      setError(err.message || 'Không thể gửi OTP. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpCode || !fullName || !password) return;

    setError('');
    setLoading(true);

    try {
      const res = await fetchAPI<{ access_token: string; refresh_token: string }>('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          phone,
          full_name: fullName,
          password,
          otp_code: otpCode,
          otp_session_id: otpSessionId,
        }),
      });

      if (res && res.access_token) {
        setToken(res.access_token);
        const session = await getSession();
        
        if (session && session.roles.includes('admin')) {
          router.push('/admin');
        } else {
          router.push('/');
        }
      }
    } catch (err: any) {
      setError(err.message || 'Đăng ký thất bại. Kiểm tra lại thông tin.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="text-center mb-8 relative">
        {step === 2 && (
          <button
            onClick={() => setStep(1)}
            className="absolute left-0 top-1/2 -translate-y-1/2 p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
        )}
        <h1 className="text-2xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>Đăng ký mới</h1>
        <p className="text-slate-500 text-sm" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
          {step === 1 ? 'Nhập số điện thoại để bắt đầu' : 'Hoàn tất thông tin tài khoản'}
        </p>
      </div>

      {error && (
        <div className="p-3 mb-6 bg-red-50 text-red-600 text-sm rounded-xl border border-red-100">
          {error}
        </div>
      )}

      {step === 1 ? (
        <form onSubmit={handleSendOtp} className="space-y-4">
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

          <button
            type="submit"
            disabled={loading || !phone}
            className="w-full mt-6 bg-gradient-to-r from-[#1a6b51] to-[#00523b] hover:from-[#00523b] hover:to-[#1a6b51] text-white font-semibold py-3 px-4 rounded-xl shadow-lg ring-1 ring-black/10 transition-all flex items-center justify-center gap-2 group disabled:opacity-70"
            style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
          >
            {loading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <>
                Tiếp tục
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </form>
      ) : (
        <form onSubmit={handleRegister} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>Mã OTP</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <KeyRound size={18} className="text-slate-400" />
              </div>
              <input
                type="text"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#1a6b51]/20 focus:border-[#1a6b51] outline-none transition-all text-sm tracking-widest font-mono"
                placeholder="123456"
                required
                style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
              />
            </div>
            <p className="text-xs text-slate-500 pt-1" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>Mã OTP đã được gửi đến số {phone}</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>Họ và tên</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User size={18} className="text-slate-400" />
              </div>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#1a6b51]/20 focus:border-[#1a6b51] outline-none transition-all text-sm"
                placeholder="Nguyễn Văn A"
                required
                style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>Mật khẩu</label>
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
              'Hoàn tất đăng ký'
            )}
          </button>
        </form>
      )}

      {step === 1 && (
        <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-center gap-1.5 text-sm">
          <span className="text-slate-500" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>Đã có tài khoản?</span>
          <Link href="/login" className="font-semibold text-[#1a6b51] hover:text-[#00523b] transition-colors" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
            Đăng nhập ngay
          </Link>
        </div>
      )}
    </>
  );
}
