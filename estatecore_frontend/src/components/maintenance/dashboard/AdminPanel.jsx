import AdminAnalytics from "./AdminAnalytics";
import SuperAdminToggles from "./SuperAdminToggles";
import RevenueLeakage from "./RevenueLeakage";
import RegulatoryDocs from "./RegulatoryDocs";

export default function AdminPanel() {
  return <div>
    <h2 className="text-xl font-bold">Admin Panel</h2>
    <AdminAnalytics />
    <SuperAdminToggles />
    <RevenueLeakage propertyId={1} />
    <RegulatoryDocs propertyId={1} />
  </div>;
}