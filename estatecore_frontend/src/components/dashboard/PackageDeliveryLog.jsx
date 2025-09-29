import { useState, useEffect } from "react";
import axios from "axios";

export default function PackageDeliveryLog({ propertyId }) {
  const [packages, setPackages] = useState([]);
  const [tenantId, setTenantId] = useState("");
  const [deliveredBy, setDeliveredBy] = useState("");

  useEffect(() => {
    fetchPackages();
  }, []);

  const fetchPackages = async () => {
    const res = await axios.get(`/api/packages/${propertyId}`);
    setPackages(res.data);
  };

  const logPackage = async () => {
    await axios.post("/api/packages", {
      property_id: propertyId,
      tenant_id: tenantId,
      delivered_by: deliveredBy
    });
    setTenantId("");
    setDeliveredBy("");
    fetchPackages();
  };

  const markPickedUp = async (id) => {
    await axios.post(`/api/packages/pickup/${id}`);
    fetchPackages();
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-2">Package Delivery Log</h2>
      <input
        type="text"
        className="border p-2 w-full mb-2"
        placeholder="Tenant ID"
        value={tenantId}
        onChange={(e) => setTenantId(e.target.value)}
      />
      <input
        type="text"
        className="border p-2 w-full mb-2"
        placeholder="Delivered By"
        value={deliveredBy}
        onChange={(e) => setDeliveredBy(e.target.value)}
      />
      <button
        className="bg-green-600 text-white px-4 py-2 rounded"
        onClick={logPackage}
      >
        Log Package
      </button>

      <div className="mt-6">
        {packages.map((p) => (
          <div key={p.id} className="border p-2 mb-2">
            <p><strong>Tenant ID:</strong> {p.tenant_id}</p>
            <p><strong>Status:</strong> {p.status}</p>
            <p><strong>Delivered by:</strong> {p.delivered_by}</p>
            <p><strong>Picked up by:</strong> {p.picked_up_by || "-"}</p>
            <p><strong>Delivered:</strong> {new Date(p.created_at).toLocaleString()}</p>
            {p.picked_up_at && (
              <p><strong>Picked up:</strong> {new Date(p.picked_up_at).toLocaleString()}</p>
            )}
            {p.status === "Delivered" && (
              <button
                className="bg-blue-600 text-white px-3 py-1 mt-2 rounded"
                onClick={() => markPickedUp(p.id)}
              >
                Mark as Picked Up
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}