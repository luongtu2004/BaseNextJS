'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import AdminLayout from '@/components/admin/AdminLayout';
import { fetchAPI } from '@/lib/api';

interface PostCategory {
  id: string;
  name: string;
}

interface PostDetail {
  id: string;
  title: string;
  slug: string;
  summary: string | null;
  content: string;
  category_id: string | null;
  post_type: string;
  status: string;
  cover_image_url: string | null;
  seo_title: string | null;
  seo_description: string | null;
  is_featured: boolean;
  allow_indexing: boolean;
}

export default function EditArticlePage() {
  const router = useRouter();
  const params = useParams();
  const id = params?.id as string;

  const [categories, setCategories] = useState<PostCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    title: '', slug: '', summary: '', content: '', category_id: '',
    post_type: 'article', status: 'draft', cover_image_url: '',
    seo_title: '', seo_description: '', is_featured: false, allow_indexing: true,
  });

  useEffect(() => {
    Promise.all([
      fetchAPI<PostDetail>(`/api/v1/admin/posts/${id}`),
      fetchAPI<PostCategory[]>('/api/v1/admin/posts/categories'),
    ]).then(([post, cats]) => {
      setCategories(cats);
      setForm({
        title: post.title,
        slug: post.slug,
        summary: post.summary ?? '',
        content: post.content,
        category_id: post.category_id ?? '',
        post_type: post.post_type,
        status: post.status,
        cover_image_url: post.cover_image_url ?? '',
        seo_title: post.seo_title ?? '',
        seo_description: post.seo_description ?? '',
        is_featured: post.is_featured,
        allow_indexing: post.allow_indexing,
      });
    }).catch((e: unknown) => {
      setError(e instanceof Error ? e.message : 'Lỗi tải bài viết');
    }).finally(() => setLoading(false));
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = {
        ...form,
        category_id: form.category_id || null,
        cover_image_url: form.cover_image_url || null,
        seo_title: form.seo_title || null,
        seo_description: form.seo_description || null,
        summary: form.summary || null,
      };
      await fetchAPI(`/api/v1/admin/posts/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
      router.push('/admin/articles');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Lỗi cập nhật bài viết');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <AdminLayout><div className="p-6 text-gray-400">⏳ Đang tải bài viết...</div></AdminLayout>;

  return (
    <AdminLayout>
      <div className="p-6 max-w-3xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-600 text-sm">← Quay lại</button>
          <h1 className="text-2xl font-bold text-gray-900">✏️ Sửa bài viết</h1>
        </div>

        {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">⚠️ {error}</div>}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <h2 className="font-semibold text-gray-700 border-b pb-2">Nội dung chính</h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tiêu đề *</label>
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Slug</label>
              <input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tóm tắt</label>
              <textarea value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })}
                rows={2} className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nội dung *</label>
              <textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })}
                rows={12} className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none resize-y" />
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <h2 className="font-semibold text-gray-700 border-b pb-2">Thiết lập</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Danh mục</label>
                <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                  <option value="">-- Không chọn --</option>
                  {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Trạng thái</label>
                <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                  <option value="draft">Nháp</option>
                  <option value="pending_review">Chờ duyệt</option>
                  <option value="published">Đã đăng</option>
                  <option value="hidden">Ẩn</option>
                  <option value="archived">Lưu trữ</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Loại bài</label>
                <select value={form.post_type} onChange={(e) => setForm({ ...form, post_type: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                  <option value="article">Bài viết</option>
                  <option value="promotion">Khuyến mãi</option>
                  <option value="announcement">Thông báo</option>
                  <option value="seo_landing">SEO Landing</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ảnh bìa URL</label>
                <input value={form.cover_image_url} onChange={(e) => setForm({ ...form, cover_image_url: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" placeholder="https://..." />
              </div>
            </div>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={form.is_featured} onChange={(e) => setForm({ ...form, is_featured: e.target.checked })} />
                Nổi bật
              </label>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={form.allow_indexing} onChange={(e) => setForm({ ...form, allow_indexing: e.target.checked })} />
                Cho phép SEO index
              </label>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <h2 className="font-semibold text-gray-700 border-b pb-2">SEO</h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">SEO Title</label>
              <input value={form.seo_title} onChange={(e) => setForm({ ...form, seo_title: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">SEO Description</label>
              <textarea value={form.seo_description} onChange={(e) => setForm({ ...form, seo_description: e.target.value })}
                rows={2} className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none" />
            </div>
          </div>

          <div className="flex gap-3 justify-end">
            <button type="button" onClick={() => router.back()} className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">Hủy</button>
            <button type="submit" disabled={saving}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg text-sm disabled:opacity-50">
              {saving ? '⏳ Đang lưu...' : '💾 Cập nhật bài viết'}
            </button>
          </div>
        </form>
      </div>
    </AdminLayout>
  );
}
