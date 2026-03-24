export default function DashboardOverview() {
  // Mock data for statistics
  const stats = [
    { title: 'Tổng bài viết', value: '128', change: '+12%' },
    { title: 'Tổng danh mục', value: '24', change: '+3%' },
    { title: 'Người dùng', value: '1,240', change: '+8%' },
    { title: 'Lượt xem', value: '24,560', change: '+5%' },
  ];

  return (
    <div>
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-600">{stat.title}</h3>
            <div className="mt-2 flex items-baseline justify-between">
              <p className="text-3xl font-bold">{stat.value}</p>
              <span className="text-sm font-medium text-green-600">{stat.change}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Hoạt động gần đây</h2>
        <div className="space-y-4">
          {[1, 2, 3].map((item) => (
            <div key={item} className="border-l-4 border-blue-500 pl-4 py-2">
              <h3 className="font-medium">Bài viết mới được thêm</h3>
              <p className="text-gray-600 text-sm">Cách sử dụng hiệu quả các dịch vụ trên nền tảng</p>
              <p className="text-gray-400 text-xs mt-1">2 giờ trước</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
