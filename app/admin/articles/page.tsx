'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import AdminLayout from '@/components/admin/AdminLayout';
import { fetchAPI } from '@/lib/api';

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

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  draft: { label: 'Nháp', color: 'bg-gray-100 text-gray-700' },
  pending_review: { label: 'Chờ duyệt', color: 'bg-yellow-100 text-yellow-700' },
  published: { label: 'Đã đăng', color: 'bg-green-100 text-green-700' },
  hidden: { label: 'Ẩn', color: 'bg-orange-100 text-orange-700' },
  archived: { label: 'Lưu trữ', color: 'bg-red-100 text-red-700' },
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
        `/api/v1/admin/posts/?${params}`
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
    <AdminLayout>
      <div className="p-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">📝 Quản lý bài viết</h1>
            <p className="text-sm text-gray-500 mt-1">Tổng: <strong>{total}</strong> bài</p>
          </div>
          <Link
            href="/admin/articles/create"
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg text-sm"
          >
            + Thêm bài viết
          </Link>
        </div>

        {/* Filter */}
        <div className="flex gap-2 mb-4 flex-wrap">
          {['', 'draft', 'published', 'pending_review', 'hidden', 'archived'].map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1); }}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                statusFilter === s
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-blue-400'
              }`}
            >
              {s === '' ? 'Tất cả' : (STATUS_LABELS[s]?.label ?? s)}
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
            ⚠️ {error} — <button onClick={load} className="underline">Thử lại</button>
          </div>
        )}

        {/* Table */}
        <div className="bg-white shadow-sm rounded-xl overflow-hidden border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Tiêu đề</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Danh mục</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Trạng thái</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Ngày tạo</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Hành động</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-gray-400">⏳ Đang tải...</td>
                </tr>
              ) : articles.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-gray-400">Không có bài viết nào.</td>
                </tr>
              ) : (
                articles.map((article) => {
                  const st = STATUS_LABELS[article.status] ?? { label: article.status, color: 'bg-gray-100 text-gray-600' };
                  return (
                    <tr key={article.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-gray-900 line-clamp-2 max-w-xs">{article.title}</div>
                        <div className="text-xs text-gray-400">{article.slug}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">{article.category?.name ?? '—'}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${st.color}`}>{st.label}</span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">
                        {new Date(article.created_at).toLocaleDateString('vi-VN')}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex items-center gap-3">
                          <Link href={`/admin/articles/${article.id}`} className="text-blue-600 hover:underline">Sửa</Link>
                          {article.status !== 'published' && (
                            <button
                              onClick={() => handleChangeStatus(article.id, 'published')}
                              className="text-green-600 hover:underline"
                            >Đăng</button>
                          )}
                          {article.status !== 'hidden' && (
                            <button
                              onClick={() => handleChangeStatus(article.id, 'hidden')}
                              className="text-orange-500 hover:underline"
                            >Ẩn</button>
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

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-4">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 rounded border text-sm disabled:opacity-40"
            >← Trước</button>
            <span className="px-3 py-1 text-sm text-gray-600">Trang {page} / {totalPages}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1 rounded border text-sm disabled:opacity-40"
            >Sau →</button>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
