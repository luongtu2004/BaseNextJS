'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchAPI } from '@/lib/api';
import {
  Plus,
  Search,
  Filter,
  MoreVertical,
  Edit3,
  Eye,
  EyeOff,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  FileText
} from 'lucide-react';

interface Article {
  id: string;
  title: string;
  slug: string;
  status: string;
  post_type: string;
  is_featured: boolean;
  view_count: number;
  published_at: string | null;
  created_at: string;
  category?: { name: string } | null;
}

const STATUS_LABELS: Record<string, { label: string; color: string; icon: any }> = {
  draft: { label: 'Bản nháp', color: 'bg-black/5 text-black/60', icon: Clock },
  pending_review: { label: 'Chờ duyệt', color: 'bg-amber-500/10 text-amber-600', icon: Clock },
  published: { label: 'Đã đăng', color: 'bg-emerald-500/10 text-emerald-600', icon: CheckCircle2 },
  hidden: { label: 'Đang ẩn', color: 'bg-orange-500/10 text-orange-600', icon: EyeOff },
  archived: { label: 'Lưu trữ', color: 'bg-red-500/10 text-red-600', icon: FileText },
};

export default function ArticlesPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const pageSize = 10;

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
      if (statusFilter) params.set('status', statusFilter);
      const data = await fetchAPI<{ items: Article[]; total: number }>(
        `/api/v1/admin/posts?${params}`
      );
      setArticles(data.items || []);
      setTotal(data.total || 0);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Lỗi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page, statusFilter]); // eslint-disable-line

  const handleChangeStatus = async (id: string, status: string) => {
    try {
      await fetchAPI(`/api/v1/admin/posts/${id}/status?status=${status}`, { method: 'PATCH' });
      load();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Lỗi cập nhật trạng thái');
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-4xl font-black uppercase tracking-tighter">Quản lý bài viết</h1>
          <p className="text-black/40 font-bold text-sm uppercase tracking-widest">
            Hệ thống có tổng cộng <span className="text-black">{total}</span> bài viết
          </p>
        </div>
        <Link
          href="/admin/articles/create"
          className="bg-black text-white px-8 py-4 rounded-[24px] font-black text-xs uppercase tracking-widest flex items-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-lg shadow-black/10"
        >
          <Plus size={18} strokeWidth={3} />
          Tạo bài viết mới
        </Link>
      </div>

      {/* Filters & Search */}
      <div className="bg-white rounded-[32px] p-4 border border-black/5 flex flex-wrap items-center gap-3 shadow-sm">
        <div className="flex-1 min-w-[300px] relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-black/20" size={18} />
          <input
            type="text"
            placeholder="Tìm kiếm tiêu đề hoặc slug..."
            className="w-full pl-12 pr-4 py-3 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold placeholder:text-black/20 outline-none transition-all"
          />
        </div>
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
          {['', 'draft', 'published', 'pending_review', 'hidden', 'archived'].map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1); }}
              className={`whitespace-nowrap px-5 py-3 rounded-[20px] text-[11px] font-black uppercase tracking-widest transition-all ${statusFilter === s
                ? 'bg-black text-white'
                : 'bg-black/[0.03] text-black/40 hover:bg-black/[0.06] hover:text-black'
                }`}
            >
              {s === '' ? 'Tất cả' : (STATUS_LABELS[s]?.label ?? s)}
            </button>
          ))}
        </div>
      </div>

      {/* Content Table */}
      <div className="bg-white rounded-[40px] border border-black/5 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-black/5 bg-black/[0.01]">
                <th className="px-8 py-6 text-[11px] font-black uppercase tracking-widest text-black/40">Bài viết</th>
                <th className="px-8 py-6 text-[11px] font-black uppercase tracking-widest text-black/40">Danh mục</th>
                <th className="px-8 py-6 text-[11px] font-black uppercase tracking-widest text-black/40">Trạng thái</th>
                <th className="px-8 py-6 text-[11px] font-black uppercase tracking-widest text-black/40 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/5">
              {loading ? (
                <tr>
                  <td colSpan={4} className="px-8 py-20 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <div className="size-6 border-2 border-black/10 border-t-black rounded-full animate-spin" />
                      <span className="text-[11px] font-black uppercase tracking-widest text-black/40">Đang tải dữ liệu...</span>
                    </div>
                  </td>
                </tr>
              ) : articles.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-8 py-20 text-center text-[11px] font-black uppercase tracking-widest text-black/20">
                    Không tìm thấy bài viết nào tương ứng
                  </td>
                </tr>
              ) : (
                articles.map((article) => {
                  const st = STATUS_LABELS[article.status] ?? { label: article.status, color: 'bg-black/5 text-black/40', icon: Clock };
                  const Icon = st.icon;
                  return (
                    <tr key={article.id} className="group hover:bg-black/[0.01] transition-all">
                      <td className="px-8 py-6">
                        <div className="flex flex-col gap-1">
                          <span className="font-black text-[15px] tracking-tight line-clamp-1 group-hover:text-blue-600 transition-colors">{article.title}</span>
                          <div className="flex items-center gap-3 text-black/30 font-bold text-[11px] uppercase tracking-tighter">
                            <span>{article.slug}</span>
                            <span className="size-1 rounded-full bg-black/10" />
                            <span>{new Date(article.created_at).toLocaleDateString('vi-VN')}</span>
                          </div>
                        </div>
                      </td>
                      <td className="px-8 py-6">
                        <span className="px-4 py-1.5 rounded-full bg-black/[0.03] text-black/60 font-black text-[11px] uppercase tracking-widest">
                          {article.category?.name ?? 'Chưa phân loại'}
                        </span>
                      </td>
                      <td className="px-8 py-6">
                        <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full font-black text-[11px] uppercase tracking-widest ${st.color}`}>
                          <Icon size={14} strokeWidth={3} />
                          {st.label}
                        </div>
                      </td>
                      <td className="px-8 py-6 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/admin/articles/${article.id}`}
                            className="size-10 rounded-full border border-black/5 flex items-center justify-center text-black/40 hover:text-black hover:bg-black/5 transition-all"
                            title="Chỉnh sửa"
                          >
                            <Edit3 size={18} />
                          </Link>
                          {article.status !== 'published' ? (
                            <button
                              onClick={() => handleChangeStatus(article.id, 'published')}
                              className="size-10 rounded-full border border-black/5 flex items-center justify-center text-emerald-500/40 hover:text-emerald-500 hover:bg-emerald-50 transition-all"
                              title="Đăng bài"
                            >
                              <CheckCircle2 size={18} />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleChangeStatus(article.id, 'hidden')}
                              className="size-10 rounded-full border border-black/5 flex items-center justify-center text-orange-500/40 hover:text-orange-500 hover:bg-orange-50 transition-all"
                              title="Ẩn bài"
                            >
                              <EyeOff size={18} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Section */}
        {totalPages > 1 && (
          <div className="px-8 py-6 bg-black/[0.01] border-t border-black/5 flex items-center justify-between">
            <p className="text-[11px] font-black uppercase tracking-widest text-black/40">
              Trang <span className="text-black">{page}</span> trên <span className="text-black">{totalPages}</span>
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="size-10 rounded-full border border-black/5 flex items-center justify-center text-black disabled:opacity-20 hover:bg-white transition-all shadow-sm"
              >
                <ChevronLeft size={20} />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="size-10 rounded-full border border-black/5 flex items-center justify-center text-black disabled:opacity-20 hover:bg-white transition-all shadow-sm"
              >
                <ChevronRight size={20} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
