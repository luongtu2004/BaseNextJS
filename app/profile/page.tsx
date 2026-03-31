'use client';

import { useAuth } from '@/contexts/AuthContext';
import {
  User,
  Phone,
  Calendar,
  MapPin,
  ShieldCheck,
  Camera,
  LogOut,
  ChevronRight,
  Settings,
  Bell,
  CreditCard,
  Heart
} from 'lucide-react';
import { motion } from 'motion/react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function ProfilePage() {
  const { user, logout, isLoading } = useAuth();
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="min-h-screen pt-32 pb-20 flex flex-col items-center justify-center gap-4">
        <div className="size-10 border-4 border-black/10 border-t-black rounded-full animate-spin" />
        <p className="text-[11px] font-black uppercase tracking-widest text-black/40">Đang tải hồ sơ...</p>
      </div>
    );
  }

  if (!user) {
    router.push('/login');
    return null;
  }

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  return (
    <div className="min-h-screen pt-32 pb-20 bg-[#F9F9F9]">
      <div className="max-w-6xl mx-auto px-6 lg:px-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">

          {/* Sidebar / Quick Info */}
          <div className="lg:col-span-4 space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-[48px] p-10 shadow-2xl shadow-black/5 border border-black/5 text-center relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-br from-black/[0.03] to-transparent" />

              <div className="relative mt-4 mb-8 inline-block group">
                <div className="size-32 rounded-[40px] bg-black/5 border-4 border-white shadow-xl flex items-center justify-center overflow-hidden">
                  {user.avatar_url ? (
                    <img src={user.avatar_url} alt={user.full_name} className="size-full object-cover" />
                  ) : (
                    <User size={48} className="text-black/10" />
                  )}
                </div>
                <button className="absolute -right-2 -bottom-2 size-10 rounded-2xl bg-black text-white flex items-center justify-center shadow-lg hover:scale-110 active:scale-95 transition-all">
                  <Camera size={18} />
                </button>
              </div>

              <h2 className="text-2xl font-black uppercase tracking-tighter mb-1">{user.full_name || 'Người dùng mới'}</h2>
              <div className="flex items-center justify-center gap-2 mb-8">
                <span className={`px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest ${user.phone_verified ? 'text-blue-600 bg-blue-500/10' : 'text-black/30 bg-black/5'
                   }`}>
                   {user.phone_verified ? 'Đã xác thực SĐT' : 'Chưa xác thực'}
                </span>
                {user.roles.includes('admin') && (
                  <span className="px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest text-white bg-black">
                    Admin
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 pt-8 border-t border-black/5">
                <div className="text-center">
                  <p className="text-xl font-black tracking-tight">0</p>
                  <p className="text-[9px] font-black uppercase tracking-widest text-black/40">Yêu cầu</p>
                </div>
                <div className="text-center border-l border-black/5">
                  <p className="text-xl font-black tracking-tight">0</p>
                  <p className="text-[9px] font-black uppercase tracking-widest text-black/40">Đánh giá</p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-[40px] p-4 shadow-xl shadow-black/5 border border-black/5"
            >
              <div className="flex flex-col gap-1">
                <Link href="/profile/edit" className="flex items-center justify-between p-4 rounded-[24px] hover:bg-black/[0.02] transition-colors group">
                  <div className="flex items-center gap-4">
                    <div className="size-11 rounded-2xl bg-black/5 flex items-center justify-center text-black/40 group-hover:bg-black group-hover:text-white transition-all">
                      <Settings size={18} />
                    </div>
                    <span className="text-sm font-black uppercase tracking-widest text-black/60">Cài đặt tài khoản</span>
                  </div>
                  <ChevronRight size={18} className="text-black/10 group-hover:text-black transition-colors" />
                </Link>
                <Link href="/profile/orders" className="flex items-center justify-between p-4 rounded-[24px] hover:bg-black/[0.02] transition-colors group">
                  <div className="flex items-center gap-4">
                    <div className="size-11 rounded-2xl bg-black/5 flex items-center justify-center text-black/40 group-hover:bg-black group-hover:text-white transition-all">
                      <CreditCard size={18} />
                    </div>
                    <span className="text-sm font-black uppercase tracking-widest text-black/60">Lịch sử giao dịch</span>
                  </div>
                  <ChevronRight size={18} className="text-black/10 group-hover:text-black transition-colors" />
                </Link>
                <Link href="/profile/favorites" className="flex items-center justify-between p-4 rounded-[24px] hover:bg-black/[0.02] transition-colors group">
                  <div className="flex items-center gap-4">
                    <div className="size-11 rounded-2xl bg-black/5 flex items-center justify-center text-black/40 group-hover:bg-red-500 group-hover:text-white transition-all">
                      <Heart size={18} />
                    </div>
                    <span className="text-sm font-black uppercase tracking-widest text-black/60">Dịch vụ đã lưu</span>
                  </div>
                  <ChevronRight size={18} className="text-black/10 group-hover:text-black transition-colors" />
                </Link>
                <button
                  onClick={handleLogout}
                  className="flex items-center justify-between p-4 rounded-[24px] hover:bg-red-50 transition-colors group mt-4 w-full"
                >
                  <div className="flex items-center gap-4">
                    <div className="size-11 rounded-2xl bg-red-500/10 flex items-center justify-center text-red-500 group-hover:bg-red-500 group-hover:text-white transition-all">
                      <LogOut size={18} />
                    </div>
                    <span className="text-sm font-black uppercase tracking-widest text-red-500">Đăng xuất</span>
                  </div>
                </button>
              </div>
            </motion.div>
          </div>

          {/* Main Info Area */}
          <div className="lg:col-span-8 space-y-8">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white rounded-[48px] p-12 shadow-2xl shadow-black/5 border border-black/5"
            >
              <div className="flex items-center justify-between mb-12">
                <h3 className="text-3xl font-black uppercase tracking-tighter">Thông tin cá nhân</h3>
                <Link href="/profile/edit" className="text-xs font-black uppercase tracking-widest text-black/30 hover:text-black transition-colors">
                  Chỉnh sửa hồ sơ
                </Link>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <div className="space-y-2">
                  <p className="text-[10px] font-black uppercase tracking-widest text-black/30 ml-1">Họ và tên</p>
                  <div className="bg-black/[0.02] p-5 rounded-[24px] border border-black/5">
                    <p className="font-bold text-black">{user.full_name || 'Chưa cập nhật'}</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-[10px] font-black uppercase tracking-widest text-black/30 ml-1">Số điện thoại</p>
                  <div className="bg-black/[0.02] p-5 rounded-[24px] border border-black/5 flex items-center gap-3">
                    <Phone size={16} className="text-black/20" />
                    <p className="font-mono font-bold text-black">{user.phone}</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-[10px] font-black uppercase tracking-widest text-black/30 ml-1">Giới tính</p>
                  <div className="bg-black/[0.02] p-5 rounded-[24px] border border-black/5">
                    <p className="font-bold text-black">{user.gender === '0' || user.gender === 0 ? 'Nam' : user.gender === '1' || user.gender === 1 ? 'Nữ' : 'Chưa xác định'}</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-[10px] font-black uppercase tracking-widest text-black/30 ml-1">Ngày sinh</p>
                  <div className="bg-black/[0.02] p-5 rounded-[24px] border border-black/5 flex items-center gap-3">
                    <Calendar size={16} className="text-black/20" />
                    <p className="font-bold text-black">
                      {user.dob ? new Date(user.dob).toLocaleDateString('vi-VN') : 'Chưa cập nhật'}
                    </p>
                  </div>
                </div>

                <div className="md:col-span-2 space-y-2">
                  <p className="text-[10px] font-black uppercase tracking-widest text-black/30 ml-1">Địa chỉ mặc định</p>
                  <div className="bg-black/[0.02] p-5 rounded-[24px] border border-black/5 flex items-center gap-3">
                    <MapPin size={16} className="text-black/20" />
                    <p className="font-bold text-black">Chưa thiết lập địa chỉ mặc định</p>
                  </div>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-black text-white rounded-[48px] p-12 shadow-2xl shadow-black/20 relative overflow-hidden"
            >
              <div className="absolute right-0 top-0 h-full w-1/3 bg-gradient-to-l from-white/10 to-transparent pointer-events-none" />
              <div className="relative z-10 flex flex-col md:flex-row items-center gap-8 justify-between">
                <div>
                  <h4 className="text-2xl font-black uppercase tracking-tighter mb-2">Xác thực SĐT</h4>
                  <p className="text-white/40 text-sm font-bold max-w-md">
                    Nâng cao độ tin cậy của tài khoản bằng cách xác thực số điện thoại để sử dụng toàn bộ tính năng trên hệ thống.
                  </p>
                </div>
                {!user.phone_verified ? (
                  <Link href="/identity/verify" className="bg-white text-black px-10 py-5 rounded-[24px] font-black text-xs uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-xl shadow-white/5 whitespace-nowrap">
                    Bắt đầu xác thực
                  </Link>
                ) : (
                  <div className="flex items-center gap-3 bg-white/10 px-8 py-4 rounded-[24px] border border-white/10 whitespace-nowrap">
                    <ShieldCheck size={20} className="text-emerald-400" />
                    <span className="font-black text-[10px] uppercase tracking-widest">SĐT đã xác thực</span>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
