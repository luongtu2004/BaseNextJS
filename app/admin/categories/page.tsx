'use client';

import { useEffect, useState } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { fetchAPI } from '@/lib/api';

interface PostCategory {
  id: string;
  code: string;
  name: string;
  slug: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

export default function CategoriesPage() {
  const [categories, setCategories] = useState<PostCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editTarget, setEditTarget] = useState<PostCategory | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ code: '', name: '', slug: '', description: '' });

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchAPI<PostCategory[]>('/api/v1/admin/posts/categories');
      setCategories(Array.isArray(data) ? data : []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Lỗi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditTarget(null);
    setForm({ code: '', name: '', slug: '', description: '' });
    setShowForm(true);
  };

  const openEdit = (cat: PostCategory) => {
    setEditTarget(cat);
    setForm({ code: cat.code, name: cat.name, slug: cat.slug, description: cat.description ?? '' });
    setShowForm(true);
  };

  const handleNameChange = (name: string) => {
    const slug = name.toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/đ/g, 'd').replace(/[^a-z0-9\s-]/g, '').trim().replace(/\s+/g, '-');
    const code = slug.replace(/-/g, '_');
    setForm((f) => ({ ...f, name, slug, code }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editTarget) {
        await fetchAPI(`/api/v1/admin/posts/categories/${editTarget.id}`, {
          method: 'PUT', body: JSON.stringify(form),
        });
      } else {
        await fetchAPI('/api/v1/admin/posts/categories', {
          method: 'POST', body: JSON.stringify(form),
        });
      }
      setShowForm(false);
      load();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Lỗi lưu dữ liệu');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (cat: PostCategory) => {
    try {
      await fetchAPI(`/api/v1/admin/posts/categories/${cat.id}`, {
        method: 'PUT',
        body: JSON.stringify({ is_active: !cat.is_active }),
      });
      load();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Lỗi');
    }
  };

  return (
    <AdminLayout>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">🗂️ Danh mục bài viết</h1>
            <p className="text-sm text-gray-500 mt-1">{categories.length} danh mục</p>
          </div>
          <button onClick={openCreate}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg text-sm">
            + Thêm danh mục
          </button>
        </div>

        {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">⚠️ {error}</div>}

        {/* Modal Form */}
        {showForm && (
          <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
            <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md mx-4">
              <h3 className="text-lg font-bold mb-4">{editTarget ? 'Sửa danh mục' : 'Tạo danh mục mới'}</h3>
              <form onSubmit={handleSubmit} className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tên danh mục *</label>
                  <input value={form.name} onChange={(e) => handleNameChange(e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Code</label>
                  <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Slug</label>
                  <input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả</label>
                  <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
                    rows={2} className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none" />
                </div>
                <div className="flex gap-2 justify-end mt-4">
                  <button type="button" onClick={() => setShowForm(false)}
                    className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">Hủy</button>
                  <button type="submit" disabled={saving}
                    className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm disabled:opacity-50">
                    {saving ? '⏳ Đang lưu...' : '💾 Lưu'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="bg-white shadow-sm rounded-xl overflow-hidden border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Tên danh mục</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Code / Slug</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Trạng thái</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Hành động</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={4} className="px-4 py-10 text-center text-gray-400">⏳ Đang tải...</td></tr>
              ) : categories.length === 0 ? (
                <tr><td colSpan={4} className="px-4 py-10 text-center text-gray-400">Chưa có danh mục nào.</td></tr>
              ) : categories.map((cat) => (
                <tr key={cat.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="text-sm font-medium text-gray-900">{cat.name}</div>
                    {cat.description && <div className="text-xs text-gray-400 mt-0.5">{cat.description}</div>}
                  </td>
                  <td className="px-4 py-3 text-xs font-mono text-gray-500">
                    <div>{cat.code}</div>
                    <div className="text-gray-400">{cat.slug}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cat.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {cat.is_active ? 'Hoạt động' : 'Ẩn'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex gap-3">
                      <button onClick={() => openEdit(cat)} className="text-blue-600 hover:underline">Sửa</button>
                      <button onClick={() => handleToggleActive(cat)} className="text-gray-500 hover:underline">
                        {cat.is_active ? 'Tắt' : 'Bật'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AdminLayout>
  );
}
