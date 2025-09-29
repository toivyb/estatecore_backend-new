import { useState } from "react";
import axios from "axios";

export default function LeaseScoring({ tenantId, propertyId }) {
  const [score, setScore] = useState(null);
  const [creditScore, setCreditScore] = useState("");
  const [latePayments, setLatePayments] = useState("");

  const calculateScore = async () => {
    const res = await axios.post("/api/lease-score", {
      tenant_id: tenantId,
      property_id: propertyId,
      credit_score: parseInt(creditScore),
      late_payments: parseInt(latePayments)
    });
    setScore(res.data);
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">AI Lease Score</h2>
      <input
        type="number"
        placeholder="Credit Score"
        value={creditScore}
        onChange={(e) => setCreditScore(e.target.value)}
        className="border p-2 w-full mb-2"
      />
      <input
        type="number"
        placeholder="Late Payments"
        value={latePayments}
        onChange={(e) => setLatePayments(e.target.value)}
        className="border p-2 w-full mb-2"
      />
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded"
        onClick={calculateScore}
      >
        Calculate Lease Score
      </button>

      {score && (
        <div className="mt-4">
          <p className="text-lg font-semibold">Score: {score.score}</p>
          <p className="text-sm text-gray-600">{score.reason}</p>
        </div>
      )}
    </div>
  );
}