'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchAPI } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { useAuth } from '@/contexts/AuthContext';
import { Phone, Lock, User, KeyRound, Loader2, ArrowRight, ArrowLeft } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import Logo from '@/components/Logo';

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();
  
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
        await login(res.access_token);
        const session = await getSession();
        
        if (session && session.roles.includes('admin')) {
          router.replace('/admin');
        } else {
          router.replace('/');
        }
      }
    } catch (err: any) {
      setError(err.message || 'Đăng ký thất bại. Kiểm tra lại thông tin.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6 }}
    >
      <div className="flex justify-center mb-8">
        <Logo iconSize={48} showText={false} />
      </div>
      <div className="text-center mb-10 relative">
        <AnimatePresence>
          {step === 2 && (
            <motion.button
              initial={{ x: -10, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -10, opacity: 0 }}
              onClick={() => setStep(1)}
              className="absolute left-0 top-1/2 -translate-y-1/2 p-3 text-slate-400 hover:text-slate-900 hover:bg-black/5 rounded-full transition-all"
            >
              <ArrowLeft size={24} strokeWidth={2.5} />
            </motion.button>
          )}
        </AnimatePresence>
        
        <h1 className="text-3xl md:text-3.5xl font-black text-slate-900 mb-3 tracking-tighter uppercase" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
          {step === 1 ? 'Đăng ký mới' : 'Xác thực tài khoản'}
        </h1>
        <p className="text-slate-500 text-[15px] font-medium" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
          {step === 1 ? 'Nhập số điện thoại để bắt đầu hành trình' : `Hoàn tất thông tin cho số ${phone}`}
        </p>
      </div>

      {error && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 mb-8 bg-red-50 text-red-600 text-sm font-bold rounded-[20px] border border-red-100 flex items-center gap-3"
        >
          <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          {error}
        </motion.div>
      )}

      <AnimatePresence mode="wait">
        {step === 1 ? (
          <motion.form 
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.5 }}
            onSubmit={handleSendOtp} 
            className="space-y-6"
          >
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

            <button
              type="submit"
              disabled={loading || !phone}
              className="w-full pt-4 group"
              style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
            >
              <div className="w-full bg-slate-900 text-white font-black py-4 px-6 rounded-[24px] shadow-[0_20px_40px_-12px_rgba(0,0,0,0.2)] hover:shadow-[0_24px_48px_-12px_rgba(0,0,0,0.3)] hover:-translate-y-0.5 transition-all flex items-center justify-center gap-3 group-disabled:opacity-70 group-disabled:pointer-events-none uppercase tracking-wider relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent pointer-events-none" />
                {loading ? (
                  <Loader2 size={24} className="animate-spin" />
                ) : (
                  <>
                    Tiếp tục xác thực
                    <ArrowRight size={20} strokeWidth={3} className="group-hover:translate-x-1.5 transition-transform" />
                  </>
                )}
              </div>
            </button>
          </motion.form>
        ) : (
          <motion.form 
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.5 }}
            onSubmit={handleRegister} 
            className="space-y-5"
          >
            <div className="space-y-2">
              <label className="text-[13px] font-black text-slate-400 uppercase tracking-widest ml-1" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
                Mã xác thực OTP
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-emerald-500 transition-colors">
                  <KeyRound size={20} strokeWidth={2.5} />
                </div>
                <input
                  type="text"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 bg-black/[0.03] border border-black/5 rounded-[24px] focus:bg-white focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 outline-none transition-all text-lg font-black tracking-widest placeholder:text-slate-300"
                  placeholder="123456"
                  required
                  style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[13px] font-black text-slate-400 uppercase tracking-widest ml-1" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
                Họ và tên
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-emerald-500 transition-colors">
                  <User size={20} strokeWidth={2.5} />
                </div>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 bg-black/[0.03] border border-black/5 rounded-[24px] focus:bg-white focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 outline-none transition-all text-base font-bold placeholder:text-slate-300"
                  placeholder="Nguyễn Văn A"
                  required
                  style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[13px] font-black text-slate-400 uppercase tracking-widest ml-1" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
                Mật khẩu
              </label>
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
              className="w-full pt-4 group"
              style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
            >
              <div className="w-full bg-emerald-600 text-white font-black py-4 px-6 rounded-[24px] shadow-[0_20px_40px_-12px_rgba(16,185,129,0.3)] hover:shadow-[0_24px_48px_-12px_rgba(16,185,129,0.4)] hover:-translate-y-0.5 transition-all flex items-center justify-center gap-3 group-disabled:opacity-70 group-disabled:pointer-events-none uppercase tracking-wider relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent pointer-events-none" />
                {loading ? (
                  <Loader2 size={24} className="animate-spin" />
                ) : (
                  'Hoàn tất đăng ký ngay'
                )}
              </div>
            </button>
          </motion.form>
        )}
      </AnimatePresence>

      {(step === 1 || !step) && (
        <div className="mt-12 pt-8 border-t border-black/5 flex flex-col items-center gap-4 text-center">
          <p className="text-slate-400 text-sm font-bold uppercase tracking-tight" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}>
            Đã có tài khoản?
          </p>
          <Link 
            href="/login" 
            className="w-full py-4 border-2 border-slate-900/5 rounded-[24px] font-black text-slate-900 hover:bg-slate-50 transition-all uppercase tracking-wider text-sm"
            style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif' }}
          >
            Đăng nhập ngay
          </Link>
        </div>
      )}
    </motion.div>
  );
}
