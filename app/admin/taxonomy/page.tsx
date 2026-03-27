'use client';

import { useEffect, useState } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { fetchAPI } from '@/lib/api';

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
    <AdminLayout>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">🏗️ Ngành nghề & Dịch vụ</h1>
            <p className="text-sm text-gray-500 mt-1">{industries.length} ngành nghề (trụ cột)</p>
          </div>
          <button onClick={openCreateIndustry}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg text-sm">
            + Thêm ngành nghề
          </button>
        </div>

        {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">⚠️ {error}</div>}

        {/* Industry Form Modal */}
        {showIndustryForm && (
          <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
            <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md mx-4">
              <h3 className="text-lg font-bold mb-4">{editIndustry ? 'Sửa ngành nghề' : 'Thêm ngành nghề mới'}</h3>
              <form onSubmit={handleIndustrySubmit} className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tên ngành nghề *</label>
                  <input value={industryForm.name} onChange={(e) => handleNameChange(e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Code</label>
                  <input value={industryForm.code} onChange={(e) => setIndustryForm({ ...industryForm, code: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả</label>
                  <textarea value={industryForm.description} onChange={(e) => setIndustryForm({ ...industryForm, description: e.target.value })}
                    rows={2} className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none" />
                </div>
                <div className="flex gap-2 justify-end mt-4">
                  <button type="button" onClick={() => setShowIndustryForm(false)}
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

        {/* Industry List */}
        <div className="space-y-3">
          {loading ? (
            <div className="text-center text-gray-400 py-10">⏳ Đang tải...</div>
          ) : industries.length === 0 ? (
            <div className="text-center text-gray-400 py-10">Chưa có ngành nghề nào.</div>
          ) : industries.map((ind) => (
            <div key={ind.id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              {/* Industry Header */}
              <div className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <button
                    onClick={() => toggleExpand(ind.id)}
                    className="text-gray-400 hover:text-gray-600 font-mono text-lg w-6 flex-shrink-0"
                  >
                    {expandedId === ind.id ? '▼' : '▶'}
                  </button>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">{ind.name}</span>
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium flex-shrink-0 ${ind.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {ind.is_active ? 'Active' : 'Ẩn'}
                      </span>
                    </div>
                    {ind.description && <p className="text-sm text-gray-400 truncate mt-0.5">{ind.description}</p>}
                    <p className="text-xs text-gray-300 font-mono">{ind.code}</p>
                  </div>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button onClick={() => openEditIndustry(ind)} className="text-xs text-blue-600 hover:underline px-2 py-1">Sửa</button>
                  <button onClick={() => toggleIndustryStatus(ind)} className="text-xs text-gray-500 hover:underline px-2 py-1">
                    {ind.is_active ? 'Tắt' : 'Bật'}
                  </button>
                </div>
              </div>

              {/* Service Categories (expanded) */}
              {expandedId === ind.id && (
                <div className="border-t border-gray-100 bg-gray-50 px-6 py-3">
                  {loadingServices[ind.id] ? (
                    <p className="text-sm text-gray-400">⏳ Đang tải dịch vụ...</p>
                  ) : (services[ind.id] ?? []).length === 0 ? (
                    <p className="text-sm text-gray-400">Chưa có dịch vụ nào trong ngành này.</p>
                  ) : (
                    <ul className="space-y-1">
                      {(services[ind.id] ?? []).map((svc) => (
                        <li key={svc.id} className="flex items-center justify-between text-sm py-1">
                          <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${svc.is_active ? 'bg-green-400' : 'bg-gray-300'}`} />
                            <span className="text-gray-700">{svc.name}</span>
                            <span className="text-gray-300 font-mono text-xs">{svc.code}</span>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </AdminLayout>
  );
}
