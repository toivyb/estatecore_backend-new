import { Routes, Route } from 'react-router-dom';
import AdminLayout from '../pages/admin/AdminLayout';
import DashboardSuperAdmin from '../pages/admin/DashboardSuperAdmin';
// Re-use your existing pages for nested routes if desired
import Properties from '../pages/Properties';
import Tenants from '../pages/Tenants';
import Managers from '../pages/Managers';
import Rent from '../pages/Rent';
import Maintenance from '../pages/Maintenance';

export default function AdminRoutes(){
  return (
    <Routes>
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<DashboardSuperAdmin />} />
        <Route path="properties" element={<Properties />} />
        <Route path="tenants" element={<Tenants />} />
        <Route path="managers" element={<Managers />} />
        <Route path="rent" element={<Rent />} />
        <Route path="maintenance" element={<Maintenance />} />
      </Route>
    </Routes>
  );
}
