import AdminLayout from '@/components/admin/AdminLayout';

export default function CategoriesPage() {
  // Mock data for categories
  const categories = [
    { id: 1, name: 'Hướng dẫn', slug: 'huong-dan', count: 24 },
    { id: 2, name: 'Giới thiệu', slug: 'gioi-thieu', count: 18 },
    { id: 3, name: 'Thông báo', slug: 'thong-bao', count: 12 },
    { id: 4, name: 'Tin tức', slug: 'tin-tuc', count: 36 },
  ];

  return (
    <AdminLayout>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Quản lý danh mục</h1>
          <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Thêm danh mục mới
          </button>
        </div>

        {/* Categories Table */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tên danh mục</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Slug</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Số bài viết</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hành động</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {categories.map((category) => (
                <tr key={category.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{category.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{category.slug}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{category.count}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <a href="#" className="text-indigo-600 hover:text-indigo-900 mr-3">Sửa</a>
                    <a href="#" className="text-red-600 hover:text-red-900">Xóa</a>
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
