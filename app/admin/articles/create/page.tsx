'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { fetchAPI } from '@/lib/api';
import {
  ArrowLeft,
  Save,
  Eye,
  Code,
  Image as ImageIcon,
  Settings,
  ChevronRight,
  Sparkles,
  Info,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface PostCategory {
  id: string;
  name: string;
}

export default function CreateArticlePage() {
  const router = useRouter();
  const [categories, setCategories] = useState<PostCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'edit' | 'preview'>('edit');

  const [form, setForm] = useState({
    title: '', slug: '', summary: '', content: '', category_id: '',
    post_type: 'article', status: 'draft', cover_image_url: '',
    seo_title: '', seo_description: '', is_featured: false, allow_indexing: true,
  });

  useEffect(() => {
    fetchAPI<PostCategory[]>('/api/v1/admin/posts/categories')
      .then(setCategories)
      .finally(() => setLoading(false));
  }, []);

  const handleTitleChange = (title: string) => {
    const slug = title
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/đ/g, 'd')
      .replace(/[^a-z0-9\s-]/g, '')
      .trim()
      .replace(/\s+/g, '-');
    setForm((f) => ({ ...f, title, slug }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) { setError('⚠️ Tiêu đề không được để trống'); return; }

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
      await fetchAPI('/api/v1/admin/posts', { method: 'POST', body: JSON.stringify(payload) });
      router.push('/admin/articles');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Lỗi tạo bài viết');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-40 gap-4">
        <div className="size-10 border-4 border-black/5 border-t-black rounded-full animate-spin" />
        <p className="text-[11px] font-black uppercase tracking-widest text-black/20">Đang chuẩn bị môi trường soạn thảo...</p>
      </div>
    );
  }

  return (
    <div className="max-w-[1400px] mx-auto space-y-8 pb-20">
      {/* Sticky Header */}
      <div className="sticky top-0 z-30 bg-background-light/80 backdrop-blur-xl -mx-4 px-4 py-4 border-b border-black/5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="size-12 rounded-full border border-black/5 flex items-center justify-center hover:bg-white transition-all shadow-sm group"
          >
            <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
          </button>
          <div className="flex flex-col">
            <h1 className="text-2xl font-black uppercase tracking-tighter">Tạo bài viết mới</h1>
            <p className="text-[10px] font-black uppercase tracking-widest text-black/40 italic">Biên tập nội dung & Tối ưu SEO</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setActiveTab(activeTab === 'edit' ? 'preview' : 'edit')}
            className="px-6 py-3 rounded-full border border-black/5 font-black text-[11px] uppercase tracking-widest flex items-center gap-2 hover:bg-white transition-all shadow-sm"
          >
            {activeTab === 'edit' ? <Eye size={16} /> : <Code size={16} />}
            {activeTab === 'edit' ? 'Xem trước' : 'Soạn thảo'}
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="bg-black text-white px-8 py-3 rounded-full font-black text-[11px] uppercase tracking-widest flex items-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-xl shadow-black/20 disabled:opacity-50"
          >
            {saving ? <div className="size-4 border-2 border-white/20 border-t-white rounded-full animate-spin" /> : <Save size={16} />}
            Xuất bản ngay
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8 space-y-8">
          <AnimatePresence mode="wait">
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-red-500/10 border border-red-500/20 text-red-600 px-6 py-4 rounded-[24px] text-sm font-bold flex items-center gap-3"
              >
                <XCircle size={18} /> {error}
              </motion.div>
            )}
          </AnimatePresence>

          <div className="bg-white rounded-[40px] border border-black/5 p-10 shadow-sm space-y-10">
            <div className="space-y-4">
              <p className="text-[11px] font-black uppercase tracking-widest text-black/20 italic ml-1">Tiêu đề bài viết</p>
              <input
                placeholder="Nhập tiêu đề ấn tượng tại đây..."
                value={form.title}
                onChange={(e) => handleTitleChange(e.target.value)}
                className="w-full text-4xl font-black bg-transparent border-none placeholder:text-black/10 focus:ring-0 outline-none tracking-tighter"
              />
              <div className="flex items-center gap-2 text-black/40 font-bold text-xs bg-black/[0.02] w-fit px-4 py-2 rounded-full">
                <span className="opacity-50">Slug:</span>
                <span className="font-mono">{form.slug || 'chua-co-slug'}</span>
              </div>
            </div>

            <div className="space-y-4 border-t border-black/5 pt-10">
              <div className="flex items-center justify-between">
                <p className="text-[11px] font-black uppercase tracking-widest text-black/20 italic ml-1">Nội dung chi tiết</p>
                <div className="flex items-center gap-4 text-[10px] font-black text-black/40 uppercase tracking-widest">
                  <span className="flex items-center gap-1.5"><Info size={12} /> Markdown được hỗ trợ</span>
                </div>
              </div>

              {activeTab === 'edit' ? (
                <textarea
                  placeholder="Bắt đầu viết những điều kỳ diệu..."
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                  className="w-full min-h-[600px] bg-black/[0.01] border border-black/5 rounded-[32px] p-8 text-lg font-medium leading-relaxed focus:bg-white focus:border-black/10 transition-all outline-none resize-none"
                />
              ) : (
                <div
                  className="w-full min-h-[600px] bg-black/[0.01] border border-black/5 rounded-[32px] p-8 prose prose-slate max-w-none prose-img:rounded-3xl"
                  dangerouslySetInnerHTML={{ __html: form.content || '<p class="text-black/20 italic">Nội dung đang trống...</p>' }}
                />
              )}
            </div>
          </div>

          {/* SEO Section */}
          <div className="bg-white rounded-[40px] border border-black/5 p-10 shadow-sm space-y-8">
            <div className="flex items-center gap-3">
              <div className="size-10 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-600 shadow-sm">
                <Sparkles size={20} />
              </div>
              <h2 className="text-xl font-black uppercase tracking-tighter">Cấu hình SEO & Metadata</h2>
            </div>

            <div className="grid grid-cols-1 gap-6">
              <div className="space-y-2">
                <div className="flex justify-between items-center ml-1">
                  <label className="text-[11px] font-black uppercase tracking-widest text-black/40">SEO Title</label>
                  <span className="text-[9px] font-black text-black/20">{form.seo_title.length}/70</span>
                </div>
                <input
                  value={form.seo_title}
                  onChange={(e) => setForm({ ...form, seo_title: e.target.value })}
                  placeholder="Hiện thị trên kết quả tìm kiếm..."
                  className="w-full px-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold outline-none transition-all"
                />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center ml-1">
                  <label className="text-[11px] font-black uppercase tracking-widest text-black/40">SEO Description</label>
                  <span className="text-[9px] font-black text-black/20">{form.seo_description.length}/160</span>
                </div>
                <textarea
                  value={form.seo_description}
                  onChange={(e) => setForm({ ...form, seo_description: e.target.value })}
                  placeholder="Mô tả ngắn gọn thu hút người dùng click..."
                  className="w-full px-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold outline-none transition-all resize-none"
                  rows={3}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 space-y-8">
          <div className="bg-white rounded-[40px] border border-black/5 p-8 shadow-sm space-y-8 sticky top-32">
            <div className="flex items-center gap-3 border-b border-black/5 pb-6">
              <Settings size={20} className="text-black/40" />
              <h2 className="text-lg font-black uppercase tracking-tighter">Thiết lập bài viết</h2>
            </div>

            <div className="space-y-6">
              <div className="space-y-3">
                <label className="text-[11px] font-black uppercase tracking-widest text-black/40">Trạng thái phát hành</label>
                <div className="grid grid-cols-3 gap-2">
                  {['draft', 'pending_review', 'published'].map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setForm({ ...form, status: s })}
                      className={`py-3 rounded-2xl text-[9px] font-black uppercase tracking-widest border transition-all ${form.status === s ? 'bg-black text-white border-black shadow-lg shadow-black/10' : 'border-black/5 text-black/40 hover:bg-black/5'
                        }`}
                    >
                      {s === 'draft' ? 'Nháp' : s === 'published' ? 'Đăng' : 'Duyệt'}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[11px] font-black uppercase tracking-widest text-black/40">Danh mục nội bộ</label>
                <select
                  value={form.category_id}
                  onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                  className="w-full px-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold outline-none transition-all appearance-none cursor-pointer"
                >
                  <option value="">Chọn danh mục...</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-[11px] font-black uppercase tracking-widest text-black/40 flex items-center justify-between">
                  Ảnh bìa hiển thị
                  <ImageIcon size={14} />
                </label>
                <input
                  placeholder="URL ảnh (https://...)"
                  value={form.cover_image_url}
                  onChange={(e) => setForm({ ...form, cover_image_url: e.target.value })}
                  className="w-full px-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-[11px] font-mono outline-none transition-all"
                />
                {form.cover_image_url && (
                  <div className="mt-4 rounded-3xl overflow-hidden aspect-video border border-black/5 relative group shadow-sm">
                    <img src={form.cover_image_url} alt="Cover" className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
                    <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                )}
              </div>

              <div className="space-y-4 pt-4 border-t border-black/5">
                <label className="flex items-center justify-between cursor-pointer group">
                  <span className="text-[11px] font-black uppercase tracking-widest text-black/40 group-hover:text-black transition-colors">Bài viết nổi bật</span>
                  <input
                    type="checkbox"
                    checked={form.is_featured}
                    onChange={(e) => setForm({ ...form, is_featured: e.target.checked })}
                    className="size-6 rounded-lg border-2 border-black/10 text-black focus:ring-black cursor-pointer"
                  />
                </label>
                <label className="flex items-center justify-between cursor-pointer group">
                  <span className="text-[11px] font-black uppercase tracking-widest text-black/40 group-hover:text-black transition-colors">Cho phép Index (SEO)</span>
                  <input
                    type="checkbox"
                    checked={form.allow_indexing}
                    onChange={(e) => setForm({ ...form, allow_indexing: e.target.checked })}
                    className="size-6 rounded-lg border-2 border-black/10 text-black focus:ring-black cursor-pointer"
                  />
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
