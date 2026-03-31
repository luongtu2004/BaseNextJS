'use client';

import { useEffect, useState } from 'react';
import { fetchAPI } from '@/lib/api';
import {
  Plus,
  Edit3,
  Power,
  PowerOff,
  X,
  Save,
  FolderTree,
  Hash,
  Link as LinkIcon,
  AlignLeft
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

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
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-4xl font-black uppercase tracking-tighter">Danh mục bài viết</h1>
          <p className="text-black/40 font-bold text-sm uppercase tracking-widest">
            Quản lý cấu trúc nội dung với <span className="text-black">{categories.length}</span> danh mục
          </p>
        </div>
        <button
          onClick={openCreate}
          className="bg-black text-white px-8 py-4 rounded-[24px] font-black text-xs uppercase tracking-widest flex items-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-lg shadow-black/10"
        >
          <Plus size={18} strokeWidth={3} />
          Thêm danh mục mới
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-600 px-6 py-4 rounded-[24px] text-sm font-bold flex items-center gap-3">
          <PowerOff size={18} /> {error}
        </div>
      )}

      {/* Modal Form */}
      <AnimatePresence>
        {showForm && (
          <div className="fixed inset-0 z-[1000] flex items-center justify-center p-6">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowForm(false)}
              className="absolute inset-0 bg-black/20 backdrop-blur-sm"
            />
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="bg-white rounded-[40px] shadow-2xl p-10 w-full max-w-xl relative overflow-hidden border border-black/5"
            >
              <div className="flex items-center justify-between mb-8">
                <h3 className="text-2xl font-black uppercase tracking-tighter">
                  {editTarget ? 'Chỉnh sửa danh mục' : 'Tạo danh mục mới'}
                </h3>
                <button onClick={() => setShowForm(false)} className="size-10 rounded-full bg-black/5 flex items-center justify-center hover:bg-black/10 transition-colors text-black/40">
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <label className="text-[11px] font-black uppercase tracking-widest text-black/40 ml-4 flex items-center gap-2">
                    <FolderTree size={12} /> Tên danh mục *
                  </label>
                  <input
                    value={form.name}
                    onChange={(e) => handleNameChange(e.target.value)}
                    placeholder="Nhập tên danh mục..."
                    className="w-full px-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold placeholder:text-black/20 outline-none transition-all"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-[11px] font-black uppercase tracking-widest text-black/40 ml-4 flex items-center gap-2">
                      <Hash size={12} /> Code
                    </label>
                    <input
                      value={form.code}
                      onChange={(e) => setForm({ ...form, code: e.target.value })}
                      className="w-full px-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-mono font-bold outline-none transition-all"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[11px] font-black uppercase tracking-widest text-black/40 ml-4 flex items-center gap-2">
                      <LinkIcon size={12} /> Slug
                    </label>
                    <input
                      value={form.slug}
                      onChange={(e) => setForm({ ...form, slug: e.target.value })}
                      className="w-full px-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-mono font-bold outline-none transition-all"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-[11px] font-black uppercase tracking-widest text-black/40 ml-4 flex items-center gap-2">
                    <AlignLeft size={12} /> Mô tả
                  </label>
                  <textarea
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    rows={3}
                    placeholder="Thông tin thêm về danh mục..."
                    className="w-full px-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold placeholder:text-black/20 outline-none transition-all resize-none"
                  />
                </div>

                <div className="flex gap-3 justify-end mt-10">
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-8 py-4 rounded-[20px] text-xs font-black uppercase tracking-widest border border-black/5 hover:bg-black/5 transition-all text-black/40 hover:text-black"
                  >
                    Hủy bỏ
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-10 py-4 bg-black text-white rounded-[20px] text-xs font-black uppercase tracking-widest disabled:opacity-50 hover:scale-105 active:scale-95 transition-all flex items-center gap-2 shadow-lg shadow-black/10"
                  >
                    {saving ? <div className="size-4 border-2 border-white/20 border-t-white rounded-full animate-spin" /> : <Save size={18} />}
                    {saving ? 'Đang lưu...' : 'Lưu danh mục'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Categories Grid - Dùng Card thay vì Table để hiện đại hơn */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full py-20 flex flex-col items-center gap-3">
            <div className="size-6 border-2 border-black/10 border-t-black rounded-full animate-spin" />
            <span className="text-[11px] font-black uppercase tracking-widest text-black/40">Đang tải danh sách...</span>
          </div>
        ) : categories.length === 0 ? (
          <div className="col-span-full py-20 text-center text-[11px] font-black uppercase tracking-widest text-black/20">
            Chưa có danh mục nào được tạo
          </div>
        ) : categories.map((cat) => (
          <div key={cat.id} className="bg-white rounded-[32px] p-8 border border-black/5 hover:border-black/10 transition-all group shadow-sm flex flex-col h-full">
            <div className="flex items-start justify-between mb-6">
              <div className={`size-12 rounded-2xl flex items-center justify-center ${cat.is_active ? 'bg-emerald-500/10 text-emerald-600' : 'bg-black/5 text-black/20'} transition-colors`}>
                <FolderTree size={24} />
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => openEdit(cat)}
                  className="size-10 rounded-full border border-black/5 flex items-center justify-center text-black/40 hover:text-black hover:bg-black/5 transition-all"
                >
                  <Edit3 size={18} />
                </button>
                <button
                  onClick={() => handleToggleActive(cat)}
                  className={`size-10 rounded-full border border-black/5 flex items-center justify-center transition-all ${cat.is_active
                    ? 'text-emerald-500/40 hover:text-emerald-500 hover:bg-emerald-50'
                    : 'text-black/40 hover:text-black hover:bg-black/5'
                    }`}
                >
                  {cat.is_active ? <Power size={18} /> : <PowerOff size={18} />}
                </button>
              </div>
            </div>

            <div className="flex-1">
              <h3 className="text-[17px] font-black tracking-tight mb-2 group-hover:text-blue-600 transition-colors uppercase">{cat.name}</h3>
              <p className="text-black/40 text-sm font-bold line-clamp-2 min-h-[2.5rem] mb-4">
                {cat.description || 'Chưa có mô tả cho danh mục này.'}
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 rounded-full bg-black/[0.03] text-black/40 font-mono text-[10px] font-bold">#{cat.code}</span>
                <span className="px-3 py-1 rounded-full bg-black/[0.03] text-black/40 font-mono text-[10px] font-bold invisible group-hover:visible transition-all">/{cat.slug}</span>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-black/5 flex items-center justify-between">
              <span className="text-[10px] font-black uppercase tracking-widest text-black/20">
                {new Date(cat.created_at).toLocaleDateString('vi-VN')}
              </span>
              <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${cat.is_active ? 'text-emerald-600 bg-emerald-500/10' : 'text-black/20 bg-black/5'
                }`}>
                <div className={`size-1.5 rounded-full ${cat.is_active ? 'bg-emerald-600' : 'bg-black/20'}`} />
                {cat.is_active ? 'Active' : 'Hidden'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
