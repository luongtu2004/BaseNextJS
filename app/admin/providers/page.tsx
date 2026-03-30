'use client';

import { useEffect, useState } from 'react';
import { fetchAPI } from '@/lib/api';
import {
  ShieldCheck,
  Store,
  Search,
  MapPin,
  Phone,
  CheckCircle2,
  AlertCircle,
  MoreHorizontal,
  ExternalLink,
  Plus
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface Provider {
  id: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
}

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const loadProviders = async () => {
    setLoading(true);
    try {
      // Giả định endpoint API cho danh sách nhà cung cấp
      const data = await fetchAPI<Provider[]>('/api/v1/admin/providers');
      setProviders(Array.isArray(data) ? data : []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Lỗi tải danh sách nhà cung cấp');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadProviders(); }, []);

  const filteredProviders = providers.filter(p =>
    p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-4xl font-black uppercase tracking-tighter">Hệ thống nhà cung cấp</h1>
          <p className="text-black/40 font-bold text-sm uppercase tracking-widest">
            Quản lý <span className="text-black">{providers.length}</span> đối tác kinh doanh trên nền tảng
          </p>
        </div>
        <button className="bg-black text-white px-8 py-4 rounded-[24px] font-black text-xs uppercase tracking-widest flex items-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-lg shadow-black/10">
          <Plus size={18} strokeWidth={3} />
          Thêm nhà cung cấp
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4 items-center bg-white p-4 rounded-[32px] border border-black/5 shadow-sm">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-black/20" size={18} />
          <input
            type="text"
            placeholder="Tìm kiếm đối tác, email, số điện thoại..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-14 pr-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold placeholder:text-black/20 outline-none transition-all"
          />
        </div>
        <div className="flex gap-2">
          <button className="px-6 py-4 rounded-[20px] bg-emerald-500/10 text-emerald-600 font-black text-[10px] uppercase tracking-widest hover:bg-emerald-500/20 transition-all border border-emerald-500/20">
            Chờ duyệt (5)
          </button>
          <button className="px-6 py-4 rounded-[20px] bg-black/[0.02] text-black/40 font-black text-[10px] uppercase tracking-widest hover:bg-black/5 transition-all">
            Tất cả đối tác
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-600 px-6 py-4 rounded-[24px] text-sm font-bold flex items-center gap-3">
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Providers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full py-20 flex flex-col items-center gap-3">
            <div className="size-6 border-2 border-black/10 border-t-black rounded-full animate-spin" />
            <span className="text-[11px] font-black uppercase tracking-widest text-black/20">Đang đồng bộ dữ liệu đối tác...</span>
          </div>
        ) : filteredProviders.length === 0 ? (
          <div className="col-span-full py-20 text-center text-[11px] font-black uppercase tracking-widest text-black/20 uppercase">
            Chưa có nhà cung cấp nào trong danh sách
          </div>
        ) : filteredProviders.map((p) => (
          <div key={p.id} className="group bg-white rounded-[32px] p-8 border border-black/5 hover:border-black/10 transition-all shadow-sm flex flex-col h-full relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute -right-10 -top-10 size-40 bg-black/[0.02] rounded-full blur-3xl group-hover:bg-black/[0.05] transition-all" />

            <div className="flex items-start justify-between mb-8 relative z-10">
              <div className="size-16 rounded-[24px] bg-black/5 border border-black/5 flex items-center justify-center font-black text-2xl group-hover:scale-110 transition-transform">
                <Store size={32} />
              </div>
              <div className="flex flex-col gap-2 items-end">
                <div className={`px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest ${p.is_verified ? 'text-blue-600 bg-blue-500/10' : 'text-orange-600 bg-orange-500/10'
                  }`}>
                  {p.is_verified ? <ShieldCheck className="inline-block mr-1" size={12} /> : null}
                  {p.is_verified ? 'Verified' : 'Unverified'}
                </div>
                <button className="size-10 rounded-full border border-black/5 flex items-center justify-center text-black/40 hover:text-black hover:bg-black/5 transition-all">
                  <MoreHorizontal size={18} />
                </button>
              </div>
            </div>

            <div className="flex-1 relative z-10">
              <h3 className="text-xl font-black tracking-tighter uppercase mb-4 group-hover:text-blue-600 transition-colors">
                {p.name}
              </h3>

              <div className="space-y-3">
                <div className="flex items-center gap-3 text-black/40 text-xs font-bold">
                  <MapPin size={14} className="shrink-0" />
                  <span className="truncate">{p.address || 'N/A'}</span>
                </div>
                <div className="flex items-center gap-3 text-black/40 text-xs font-bold">
                  <Phone size={14} className="shrink-0" />
                  <span>{p.phone || 'N/A'}</span>
                </div>
              </div>
            </div>

            <div className="mt-10 pt-8 border-t border-black/5 flex items-center justify-between relative z-10">
              <button className="text-[10px] font-black uppercase tracking-widest text-black hover:text-blue-600 flex items-center gap-1.5 transition-colors">
                Chi tiết hồ sơ <ExternalLink size={12} strokeWidth={3} />
              </button>
              <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest ${p.is_active ? 'text-emerald-700 bg-emerald-500/10' : 'text-black/20 bg-black/5'
                }`}>
                {p.is_active ? <CheckCircle2 size={12} strokeWidth={3} /> : <AlertCircle size={12} strokeWidth={3} />}
                {p.is_active ? 'Active' : 'Locked'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
