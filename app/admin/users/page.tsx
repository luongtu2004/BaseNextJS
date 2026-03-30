'use client';

import { useEffect, useState } from 'react';
import { fetchAPI } from '@/lib/api';
import { 
  Users, 
  UserPlus, 
  Search, 
  Mail, 
  Shield, 
  MoreVertical, 
  UserCheck, 
  UserX,
  Filter,
  Calendar,
  Phone,
  Lock,
  Unlock,
  Trash2,
  X,
  CheckCircle2,
  AlertCircle,
  Hash,
  Edit2
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface User {
  id: string;
  phone: string;
  full_name: string;
  roles: string[];
  gender: number | null;
  dob: string | null;
  status: 'active' | 'pending_activation' | 'suspended' | 'blocked' | 'deleted';
  created_at: string;
  avatar_url?: string;
  identity_verified: boolean;
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [userForm, setUserForm] = useState({
    phone: '',
    full_name: '',
    password: '',
    gender: 0,
    dob: '',
    avatar_url: ''
  });

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '10'
      });
      if (roleFilter) params.append('role', roleFilter);
      if (statusFilter) params.append('status', statusFilter);
      
      const data = await fetchAPI<{ items: User[], total: number }>('/api/v1/admin/users/?' + params.toString());
      setUsers(data.items || []);
      setTotal(data.total || 0);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Lỗi kết nối máy chủ');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadUsers(); }, [page, roleFilter, statusFilter]);

  const handleUpdateStatus = async (userId: string, status: string) => {
    try {
      await fetchAPI(`/api/v1/admin/users/${userId}/status?status=${status}`, { method: 'PATCH' });
      loadUsers();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Lỗi cập nhật trạng thái');
    }
  };

  const openCreateModal = () => {
    setEditUser(null);
    setUserForm({ phone: '', full_name: '', password: '', gender: 0, dob: '', avatar_url: '' });
    setIsModalOpen(true);
  };

  const openEditModal = (user: User) => {
    setEditUser(user);
    setUserForm({
      phone: user.phone || '',
      full_name: user.full_name || '',
      password: '', // Don't show password
      gender: user.gender ?? 0,
      dob: user.dob ? new Date(user.dob).toISOString().split('T')[0] : '',
      avatar_url: user.avatar_url || ''
    });
    setIsModalOpen(true);
  };

  const handleUserSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      if (editUser) {
        // Only send fields that can be updated
        const updateData = {
          full_name: userForm.full_name,
          gender: userForm.gender,
          dob: userForm.dob,
          avatar_url: userForm.avatar_url
        };
        await fetchAPI(`/api/v1/admin/users/${editUser.id}`, {
          method: 'PUT',
          body: JSON.stringify(updateData)
        });
      } else {
        await fetchAPI('/api/v1/admin/users/create-provider-owner', {
          method: 'POST',
          body: JSON.stringify(userForm)
        });
      }
      setIsModalOpen(false);
      loadUsers();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Lỗi lưu thông tin người dùng');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Bạn có chắc chắn muốn xóa (vô hiệu hóa) người dùng này?')) return;
    try {
      await fetchAPI(`/api/v1/admin/users/${userId}`, { method: 'DELETE' });
      loadUsers();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Lỗi khi xóa người dùng');
    }
  };

  const filteredUsers = users.filter(u => 
    u.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.phone?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-4xl font-black uppercase tracking-tighter">Quản lý Thành viên</h1>
          <p className="text-black/40 font-bold text-sm uppercase tracking-widest">
            Điều hành <span className="text-black">{total}</span> tài khoản trong hệ thống
          </p>
        </div>
        <button 
          onClick={openCreateModal}
          className="bg-black text-white px-8 py-4 rounded-[24px] font-black text-xs uppercase tracking-widest flex items-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-lg shadow-black/10"
        >
          <UserPlus size={18} strokeWidth={3} />
          Thêm Quản lý/Đối tác
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4 items-center bg-white p-4 rounded-[32px] border border-black/5 shadow-sm overflow-x-auto no-scrollbar">
        <div className="relative flex-1 min-w-[300px]">
          <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-black/20" size={18} />
          <input 
            type="text"
            placeholder="Tìm kiếm theo tên hoặc số điện thoại..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-14 pr-6 py-4 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold placeholder:text-black/20 outline-none transition-all"
          />
        </div>
        
        <div className="flex gap-2 shrink-0">
          <select 
             value={roleFilter}
             onChange={(e) => {setRoleFilter(e.target.value); setPage(1);}}
             className="px-6 py-4 rounded-[20px] bg-black/[0.02] text-black font-black text-[11px] uppercase tracking-widest border-none outline-none focus:bg-black/5 cursor-pointer appearance-none"
          >
             <option value="">Tất cả vai trò</option>
             <option value="admin">Quản trị viên</option>
             <option value="provider_owner">Chủ doanh nghiệp</option>
             <option value="customer">Khách hàng</option>
          </select>

          <select 
             value={statusFilter}
             onChange={(e) => {setStatusFilter(e.target.value); setPage(1);}}
             className="px-6 py-4 rounded-[20px] bg-black/[0.02] text-black font-black text-[11px] uppercase tracking-widest border-none outline-none focus:bg-black/5 cursor-pointer appearance-none"
          >
             <option value="">Mọi trạng thái</option>
             <option value="active">Hoạt động</option>
             <option value="blocked">Đã khóa</option>
             <option value="pending_activation">Chờ kích hoạt</option>
             <option value="deleted">Đã xóa</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-600 px-6 py-4 rounded-[24px] text-sm font-bold flex items-center gap-3">
           <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Users Table */}
      <div className="bg-white rounded-[40px] border border-black/5 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-black/10 bg-black/[0.01]">
                <th className="px-8 py-6 text-[11px] font-black uppercase tracking-widest text-black/40">Thành viên</th>
                <th className="px-8 py-6 text-[11px] font-black uppercase tracking-widest text-black/40">Vai trò</th>
                <th className="px-8 py-6 text-[11px] font-black uppercase tracking-widest text-black/40">Trạng thái</th>
                <th className="px-8 py-6 text-[11px] font-black uppercase tracking-widest text-black/40">Ngày tham gia</th>
                <th className="px-8 py-6 text-[11px] font-black uppercase tracking-widest text-black/40 text-right">Quản lý</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/5">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-24 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <div className="size-6 border-2 border-black/10 border-t-black rounded-full animate-spin" />
                      <span className="text-[11px] font-black uppercase tracking-widest text-black/20">Đang chuẩn bị danh sách...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-24 text-center text-[11px] font-black uppercase tracking-widest text-black/10 italic">
                    Không có kết quả nào được tìm thấy
                  </td>
                </tr>
              ) : users.map((u) => (
                <tr key={u.id} className="group hover:bg-black/[0.01] transition-all">
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-4">
                      <div className="size-12 rounded-[18px] bg-black/5 border border-black/5 flex items-center justify-center font-black text-sm group-hover:scale-110 transition-transform relative">
                        {u.avatar_url ? (
                          <img src={u.avatar_url} alt={u.full_name} className="size-full object-cover rounded-[18px]" />
                        ) : (
                          u.full_name?.charAt(0) || <Users size={18} />
                        )}
                        {u.identity_verified && (
                          <div className="absolute -right-1 -bottom-1 size-5 bg-blue-500 rounded-full border-2 border-white flex items-center justify-center text-white" title="Đã xác thực">
                            <CheckCircle2 size={10} strokeWidth={4} />
                          </div>
                        )}
                      </div>
                      <div>
                        <p className="font-black text-[15px] tracking-tight group-hover:text-blue-600 transition-colors uppercase">{u.full_name || 'Anonymous'}</p>
                        <div className="flex items-center gap-1.5 text-black/30 text-[10px] font-black uppercase tracking-wider">
                          <Phone size={10} /> {u.phone}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex flex-wrap gap-1.5">
                      {u.roles?.map(role => (
                        <span key={role} className={`inline-flex items-center gap-1 px-3 py-1 rounded-full font-black text-[8px] uppercase tracking-widest ${
                          role === 'admin' ? 'bg-black text-white' : 'bg-black/5 text-black'
                        }`}>
                          <Shield size={10} /> {role.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest ${
                      u.status === 'active' ? 'text-emerald-600 bg-emerald-500/10 border border-emerald-500/20' : 
                      u.status === 'deleted' ? 'text-black/20 bg-black/5' :
                      'text-red-500 bg-red-500/10 border border-red-500/20'
                    }`}>
                      <div className={`size-1.5 rounded-full ${u.status === 'active' ? 'bg-emerald-600' : u.status === 'deleted' ? 'bg-black/20' : 'bg-red-500'}`} />
                      {u.status === 'active' ? 'Hoạt động' : u.status === 'deleted' ? 'Đã xóa' : u.status}
                    </div>
                  </td>
                  <td className="px-8 py-6 font-bold text-black/40 text-[12px] tracking-tight">
                    <div className="flex items-center gap-2 font-black uppercase text-[10px] tracking-widest">
                      <Calendar size={14} className="opacity-40" />
                      {new Date(u.created_at).toLocaleDateString('vi-VN')}
                    </div>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-all scale-95 group-hover:scale-100">
                      <button 
                         onClick={() => openEditModal(u)}
                         className="size-10 rounded-full border border-black/5 flex items-center justify-center text-black/40 hover:text-black hover:bg-black/5 transition-all shadow-sm"
                         title="Chỉnh sửa"
                      >
                         <Edit2 size={18} />
                      </button>
                      {u.status === 'active' ? (
                         <button 
                          onClick={() => handleUpdateStatus(u.id, 'blocked')}
                          className="size-10 rounded-full border border-black/5 flex items-center justify-center text-red-500/40 hover:text-red-500 hover:bg-red-50 transition-all shadow-sm"
                          title="Khóa tài khoản"
                         >
                          <Lock size={18} />
                         </button>
                      ) : (
                        <button 
                          onClick={() => handleUpdateStatus(u.id, 'active')}
                          className="size-10 rounded-full border border-black/5 flex items-center justify-center text-emerald-500/40 hover:text-emerald-500 hover:bg-emerald-50 transition-all shadow-sm"
                          title="Mở khóa tài khoản"
                        >
                          <Unlock size={18} />
                        </button>
                      )}
                      <button 
                        onClick={() => handleDeleteUser(u.id)}
                        className="size-10 rounded-full border border-black/5 flex items-center justify-center text-black/20 hover:text-red-600 hover:bg-red-50 transition-all shadow-sm"
                        title="Xóa vĩnh viễn"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="px-8 py-6 border-t border-black/5 flex items-center justify-between bg-black/[0.01]">
           <p className="text-[10px] font-black uppercase tracking-widest text-black/30">
             Hiển thị {users.length} trên tổng số {total}
           </p>
           <div className="flex gap-2">
              <button 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 rounded-xl border border-black/5 bg-white text-[10px] font-black uppercase tracking-widest hover:bg-black hover:text-white transition-all disabled:opacity-30 disabled:hover:bg-white disabled:hover:text-black"
              >
                Trước
              </button>
              <button 
                onClick={() => setPage(p => p + 1)}
                disabled={users.length < 10}
                className="px-4 py-2 rounded-xl border border-black/5 bg-white text-[10px] font-black uppercase tracking-widest hover:bg-black hover:text-white transition-all disabled:opacity-30 disabled:hover:bg-white disabled:hover:text-black"
              >
                Sau
              </button>
           </div>
        </div>
      </div>

      {/* Create/Edit User Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
             <motion.div 
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               exit={{ opacity: 0 }}
               onClick={() => setIsModalOpen(false)}
               className="absolute inset-0 bg-black/60 backdrop-blur-sm"
             />
             <motion.div 
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="relative bg-white rounded-[40px] w-full max-w-xl p-10 shadow-2xl overflow-hidden"
             >
                {/* Modal Glow */}
                <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-blue-500 via-purple-500 to-black" />
                
                <div className="flex items-center justify-between mb-8">
                   <div className="flex flex-col">
                      <h2 className="text-2xl font-black uppercase tracking-tighter">
                         {editUser ? 'Chỉnh Sửa Thành Viên' : 'Thêm Thành Viên Mới'}
                      </h2>
                      <p className="text-black/40 text-[10px] font-black uppercase tracking-widest italic font-mono">
                         {editUser ? `ID: ${editUser.id}` : 'Tạo tài khoản đối tác / quản lý'}
                      </p>
                   </div>
                   <button onClick={() => setIsModalOpen(false)} className="size-10 rounded-full border border-black/5 flex items-center justify-center text-black/30 hover:text-black hover:bg-black/5 transition-all">
                      <X size={20} />
                   </button>
                </div>

                <form onSubmit={handleUserSubmit} className="space-y-6">
                   <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2 col-span-2 md:col-span-1">
                         <label className="text-[10px] font-black uppercase tracking-widest text-black/40 ml-1">Họ và tên</label>
                         <div className="relative">
                            <Users size={16} className="absolute left-5 top-1/2 -translate-y-1/2 text-black/20" />
                            <input 
                              required
                              value={userForm.full_name}
                              onChange={(e) => setUserForm({...userForm, full_name: e.target.value})}
                              className="w-full pl-12 pr-6 py-3.5 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold placeholder:text-black/10 transition-all outline-none"
                              placeholder="Nguyen Van A"
                            />
                         </div>
                      </div>
                      <div className="space-y-2 col-span-2 md:col-span-1">
                         <label className="text-[10px] font-black uppercase tracking-widest text-black/40 ml-1">Số điện thoại *</label>
                         <div className="relative">
                            <Hash size={16} className="absolute left-5 top-1/2 -translate-y-1/2 text-black/20" />
                            <input 
                              required
                              disabled={!!editUser}
                              value={userForm.phone}
                              onChange={(e) => setUserForm({...userForm, phone: e.target.value})}
                              className="w-full pl-12 pr-6 py-3.5 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold placeholder:text-black/10 transition-all outline-none font-mono disabled:opacity-50"
                              placeholder="0987xxx..."
                            />
                         </div>
                      </div>
                   </div>

                   {!editUser && (
                     <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-black/40 ml-1">Mật khẩu khởi tạo *</label>
                        <div className="relative">
                           <Lock size={16} className="absolute left-5 top-1/2 -translate-y-1/2 text-black/20" />
                           <input 
                             required
                             type="password"
                             value={userForm.password}
                             onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                             className="w-full pl-12 pr-6 py-3.5 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold placeholder:text-black/10 transition-all outline-none"
                             placeholder="••••••••"
                           />
                        </div>
                     </div>
                   )}

                   <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-black/40 ml-1">Giới tính</label>
                        <select 
                          value={userForm.gender}
                          onChange={(e) => setUserForm({...userForm, gender: parseInt(e.target.value)})}
                          className="w-full px-6 py-3.5 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold outline-none appearance-none cursor-pointer"
                        >
                          <option value={0}>Nam</option>
                          <option value={1}>Nữ</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-black/40 ml-1">Ngày sinh</label>
                        <input 
                          type="date"
                          value={userForm.dob}
                          onChange={(e) => setUserForm({...userForm, dob: e.target.value})}
                          className="w-full px-6 py-3.5 bg-black/[0.02] border border-transparent focus:border-black/10 rounded-[20px] text-sm font-bold outline-none uppercase"
                        />
                      </div>
                   </div>

                   <div className="flex gap-4 pt-6">
                      <button 
                        type="button"
                        onClick={() => setIsModalOpen(false)}
                        className="flex-1 py-4 border border-black/5 rounded-[24px] font-black text-[11px] uppercase tracking-widest hover:bg-black/5 transition-all outline-none"
                      >
                         Hủy bỏ
                      </button>
                      <button 
                         type="submit"
                         disabled={isSaving}
                         className="flex-1 py-4 bg-black text-white rounded-[24px] font-black text-[11px] uppercase tracking-widest shadow-xl shadow-black/20 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50"
                      >
                         {isSaving ? 'Đang lưu...' : (editUser ? 'Cập nhật' : 'Xác nhận tạo')}
                      </button>
                   </div>
                </form>
             </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
