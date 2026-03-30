'use client';

import { useEffect, useState } from 'react';
import { fetchAPI } from '@/lib/api';
import { 
  Plus, 
  ChevronDown, 
  ChevronRight, 
  Settings2, 
  Power, 
  PowerOff, 
  X, 
  Save, 
  Layers,
  Fingerprint,
  FileText,
  Briefcase
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface IndustryCategory {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

interface ServiceCategory {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
}

export default function TaxonomyPage() {
  const [industries, setIndustries] = useState<IndustryCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [services, setServices] = useState<Record<string, ServiceCategory[]>>({});
  const [loadingServices, setLoadingServices] = useState<Record<string, boolean>>({});

  // Industry form
  const [showIndustryForm, setShowIndustryForm] = useState(false);
  const [editIndustry, setEditIndustry] = useState<IndustryCategory | null>(null);
  const [industryForm, setIndustryForm] = useState({ code: '', name: '', description: '' });
  const [saving, setSaving] = useState(false);

  const loadIndustries = async () => {
    setLoading(true);
    try {
      const data = await fetchAPI<IndustryCategory[]>('/api/v1/admin/industry-categories');
      setIndustries(Array.isArray(data) ? data : []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Lỗi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadIndustries(); }, []);

  const toggleExpand = async (industryId: string) => {
    if (expandedId === industryId) { setExpandedId(null); return; }
    setExpandedId(industryId);
    if (!services[industryId]) {
      setLoadingServices((s) => ({ ...s, [industryId]: true }));
      try {
        const data = await fetchAPI<ServiceCategory[]>(`/api/v1/admin/service-categories?industry_category_id=${industryId}`);
        setServices((s) => ({ ...s, [industryId]: Array.isArray(data) ? data : [] }));
      } catch { /* ignore */ }
      setLoadingServices((s) => ({ ...s, [industryId]: false }));
    }
  };

  const toggleIndustryStatus = async (ind: IndustryCategory) => {
    try {
      await fetchAPI(`/api/v1/admin/industry-categories/${ind.id}/status`, {
        method: 'PATCH', body: JSON.stringify({ is_active: !ind.is_active }),
      });
      loadIndustries();
    } catch (e: unknown) { alert(e instanceof Error ? e.message : 'Lỗi'); }
  };

  const openCreateIndustry = () => {
    setEditIndustry(null);
    setIndustryForm({ code: '', name: '', description: '' });
    setShowIndustryForm(true);
  };

  const openEditIndustry = (ind: IndustryCategory) => {
    setEditIndustry(ind);
    setIndustryForm({ code: ind.code, name: ind.name, description: ind.description ?? '' });
    setShowIndustryForm(true);
  };

  const handleNameChange = (name: string) => {
    const code = name.toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/đ/g, 'd').replace(/[^a-z0-9\s]/g, '').trim().replace(/\s+/g, '_');
    setIndustryForm((f) => ({ ...f, name, code }));
  };

  const handleIndustrySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editIndustry) {
        await fetchAPI(`/api/v1/admin/industry-categories/${editIndustry.id}`, {
          method: 'PUT', body: JSON.stringify(industryForm),
        });
      } else {
        await fetchAPI('/api/v1/admin/industry-categories', {
          method: 'POST', body: JSON.stringify(industryForm),
        });
      }
      setShowIndustryForm(false);
      loadIndustries();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Lỗi lưu');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-4xl font-black uppercase tracking-tighter">Ngành nghề & Dịch vụ</h1>
          <p className="text-black/40 font-bold text-sm uppercase tracking-widest">
            Phân loại hệ sinh thái với <span className="text-black">{industries.length}</span> trụ cột ngành nghề
          </p>
        </div>
        <button 
          onClick={openCreateIndustry}
          className="bg-black text-white px-8 py-4 rounded-[24px] font-black text-xs uppercase tracking-widest flex items-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-lg shadow-black/10"
        >
          <Plus size={18} strokeWidth={3} />
          Thêm ngành nghề
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-600 px-6 py-4 rounded-[24px] text-sm font-bold flex items-center gap-3">
           <PowerOff size={18} /> {error}
        </div>
      )}

      {/* Industry Form Modal */}
      <AnimatePresence>
        {showIndustryForm && (
          <div className="fixed inset-0 z-[1000] flex items-center justify-center p-6">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowIndustryForm(false)}
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
                  {editIndustry ? 'Chỉnh sửa ngành nghề' : 'Thêm ngành nghề mới'}
                </h3>
                <button onClick={() => setShowIndustryForm(false)} className="size-10 rounded-full bg-black/5 flex items-center justify-center hover:bg-black/10 transition-colors text-black/40">
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleIndustrySubmit} className="space-y-6">
                <div className="space-y-2">
                  <label className="text-[11px] font-black uppercase tracking-widest text-black/40 ml-4 flex items-center gap-2">
                    <Briefcase size={12} /> Tên ngành nghề *
                  </label>
                  <input 
                    value={industryForm.name} 
                    onChange={(e) => handleNameChange(e.target.value)}
                    placeholder="Nhập tên ngành nghề (VD: Xây dựng, CNTT...)"
                    className="w-full px-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold placeholder:text-black/20 outline-none transition-all"
                    required 
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-[11px] font-black uppercase tracking-widest text-black/40 ml-4 flex items-center gap-2">
                    <Fingerprint size={12} /> Mã định danh (Code)
                  </label>
                  <input 
                    value={industryForm.code} 
                    onChange={(e) => setIndustryForm({ ...industryForm, code: e.target.value })}
                    className="w-full px-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-mono font-bold outline-none transition-all"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-[11px] font-black uppercase tracking-widest text-black/40 ml-4 flex items-center gap-2">
                    <FileText size={12} /> Mô tả ngành
                  </label>
                  <textarea 
                    value={industryForm.description} 
                    onChange={(e) => setIndustryForm({ ...industryForm, description: e.target.value })}
                    rows={3} 
                    placeholder="Thông tin thêm về ngành nghề này..."
                    className="w-full px-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold placeholder:text-black/20 outline-none transition-all resize-none"
                  />
                </div>

                <div className="flex gap-3 justify-end mt-10">
                  <button 
                    type="button" 
                    onClick={() => setShowIndustryForm(false)}
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
                    {saving ? 'Đang lưu...' : 'Lưu ngành nghề'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Industry List */}
      <div className="grid grid-cols-1 gap-4">
        {loading ? (
          <div className="py-20 flex flex-col items-center gap-3">
            <div className="size-6 border-2 border-black/10 border-t-black rounded-full animate-spin" />
            <span className="text-[11px] font-black uppercase tracking-widest text-black/40">Đang đồng bộ dữ liệu...</span>
          </div>
        ) : industries.length === 0 ? (
          <div className="py-20 text-center text-[11px] font-black uppercase tracking-widest text-black/20 uppercase">
            Chưa có dữ liệu ngành nghề
          </div>
        ) : industries.map((ind) => (
          <div key={ind.id} className="group bg-white rounded-[32px] border border-black/5 hover:border-black/10 transition-all overflow-hidden">
            {/* Industry Header */}
            <div className="flex items-center justify-between p-6 md:p-8">
              <div className="flex items-center gap-6 flex-1 min-w-0">
                <button
                  onClick={() => toggleExpand(ind.id)}
                  className={`size-12 rounded-2xl flex items-center justify-center transition-all ${
                    expandedId === ind.id ? 'bg-black text-white' : 'bg-black/[0.03] text-black/40 hover:text-black'
                  }`}
                >
                  {expandedId === ind.id ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                </button>
                <div className="min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-xl font-black tracking-tighter uppercase">{ind.name}</h3>
                    <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-widest ${
                      ind.is_active ? 'text-emerald-600 bg-emerald-500/10' : 'text-black/20 bg-black/5'
                    }`}>
                      <div className={`size-1.5 rounded-full ${ind.is_active ? 'bg-emerald-600' : 'bg-black/20'}`} />
                      {ind.is_active ? 'Active' : 'Hidden'}
                    </div>
                  </div>
                  {ind.description && <p className="text-black/40 text-sm font-bold truncate max-w-2xl">{ind.description}</p>}
                  <p className="text-[10px] font-black text-black/20 tracking-widest uppercase mt-1 font-mono">{ind.code}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
                <button 
                  onClick={() => openEditIndustry(ind)} 
                  className="size-11 rounded-full border border-black/5 flex items-center justify-center text-black/40 hover:text-black hover:bg-black/5 transition-all"
                >
                  <Settings2 size={18} />
                </button>
                <button 
                  onClick={() => toggleIndustryStatus(ind)} 
                  className={`size-11 rounded-full border border-black/5 flex items-center justify-center transition-all ${
                    ind.is_active ? 'text-emerald-500/40 hover:text-emerald-500 hover:bg-emerald-50' : 'text-black/40 hover:text-black hover:bg-black/5'
                  }`}
                >
                  {ind.is_active ? <Power size={18} /> : <PowerOff size={18} />}
                </button>
              </div>
            </div>

            {/* Service Categories (expanded) */}
            <AnimatePresence>
              {expandedId === ind.id && (
                <motion.div 
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-black/5 bg-black/[0.01]"
                >
                  <div className="p-8 md:pl-24 md:pr-12">
                    <div className="flex items-center gap-2 mb-6">
                      <Layers size={14} className="text-black/20" />
                      <span className="text-[11px] font-black uppercase tracking-widest text-black/40">Danh sách dịch vụ cung cấp</span>
                    </div>

                    {loadingServices[ind.id] ? (
                      <div className="flex items-center gap-3 py-4">
                        <div className="size-4 border-2 border-black/10 border-t-black rounded-full animate-spin" />
                        <span className="text-[11px] font-bold text-black/20 italic">Đang truy xuất dịch vụ...</span>
                      </div>
                    ) : (services[ind.id] ?? []).length === 0 ? (
                      <div className="py-8 text-[11px] font-bold text-black/20 uppercase tracking-widest italic">
                        Chưa có dịch vụ nào được cấu hình cho ngành này
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {(services[ind.id] ?? []).map((svc) => (
                          <div key={svc.id} className="flex items-center gap-4 bg-white p-4 rounded-[20px] border border-black/5 hover:border-black/10 transition-all shadow-sm">
                            <div className={`size-2.5 rounded-full flex-shrink-0 ${svc.is_active ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]' : 'bg-black/10'}`} />
                            <div className="min-w-0">
                              <p className="text-sm font-black tracking-tight text-black truncate uppercase">{svc.name}</p>
                              <p className="text-[9px] font-mono font-bold text-black/20 uppercase mt-0.5">{svc.code}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </div>
  );
}
