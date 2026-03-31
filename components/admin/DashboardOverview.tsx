import { ArrowUpRight, Users, FileText, FolderTree, Eye } from 'lucide-react';

export default function DashboardOverview() {
  const stats = [
    { title: 'Tổng bài viết', value: '128', change: '+12%', icon: FileText, color: 'text-blue-500', bg: 'bg-blue-500/5' },
    { title: 'Tổng danh mục', value: '24', change: '+3%', icon: FolderTree, color: 'text-emerald-500', bg: 'bg-emerald-500/5' },
    { title: 'Người dùng', value: '1,240', change: '+8%', icon: Users, color: 'text-orange-500', bg: 'bg-orange-500/5' },
    { title: 'Lượt xem', value: '24,560', change: '+5%', icon: Eye, color: 'text-purple-500', bg: 'bg-purple-500/5' },
  ];

  return (
    <div className="space-y-10">
      {/* Page Title Section */}
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-black uppercase tracking-tighter">Tổng quan hệ thống</h1>
        <p className="text-black/40 font-bold text-sm uppercase tracking-widest">Dữ liệu thời gian thực và phân tích</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-[32px] p-8 border border-black/5 hover:border-black/10 transition-all group shadow-sm">
            <div className="flex items-start justify-between mb-6">
              <div className={`size-14 ${stat.bg} rounded-2xl flex items-center justify-center ${stat.color} group-hover:scale-110 transition-transform duration-300`}>
                <stat.icon size={28} strokeWidth={2.5} />
              </div>
              <div className="flex items-center gap-1 text-emerald-500 font-black text-xs bg-emerald-500/10 px-2 py-1 rounded-full">
                <ArrowUpRight size={14} strokeWidth={3} />
                {stat.change}
              </div>
            </div>
            <div>
              <p className="text-black/40 font-bold text-[11px] uppercase tracking-widest mb-1">{stat.title}</p>
              <p className="text-3xl font-black tracking-tighter">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity Section */}
      <div className="bg-white rounded-[40px] p-10 border border-black/5 shadow-sm">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-black uppercase tracking-tighter">Hoạt động mới nhất</h2>
          <button className="text-[11px] font-black uppercase tracking-widest text-black/40 hover:text-black transition-colors">Xem tất cả</button>
        </div>
        
        <div className="space-y-6">
          {[1, 2, 3].map((item) => (
            <div key={item} className="flex items-center gap-6 group cursor-pointer p-2 rounded-[24px] hover:bg-black/[0.02] transition-all">
              <div className="size-12 rounded-full border border-black/5 flex items-center justify-center font-black text-sm bg-white shrink-0 shadow-sm group-hover:border-black/10 transition-all">
                {item}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-black text-[15px] tracking-tight group-hover:text-blue-600 transition-colors">Bài viết mới được thêm vào hệ thống</h3>
                <p className="text-black/40 text-sm font-bold truncate">Cách sử dụng hiệu quả các dịch vụ trên nền tảng Sàn Dịch Vụ</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-black/40 text-[10px] font-black uppercase tracking-tighter">Mới đây</p>
                <p className="text-[11px] font-black uppercase tracking-widest mt-0.5">2 GIỜ TRƯỚC</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

