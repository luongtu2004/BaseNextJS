import AdminLayout from '@/components/admin/AdminLayout';
import DashboardOverview from '@/components/admin/DashboardOverview';

export default function AdminDashboard() {
  return (
    <AdminLayout>
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6">Trang tổng quan quản trị</h1>
        <DashboardOverview />
      </div>
    </AdminLayout>
  );
}
