import React, { useState } from "react";
import axios from "axios";

export default function VisitorPassGenerator({ propertyId, issuedByUserId, onCreated }) {
  const [visitorName, setVisitorName] = useState("");
  const [validFrom, setValidFrom] = useState("");
  const [validUntil, setValidUntil] = useState("");
  const [code, setCode] = useState("");

  const createPass = async () => {
    const res = await axios.post("/api/visitor_pass", {
      property_id: propertyId,
      issued_by_user_id: issuedByUserId,
      visitor_name: visitorName,
      valid_from: validFrom,
      valid_until: validUntil,
    });
    setCode(res.data.code);
    onCreated && onCreated();
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow mt-4">
      <div className="mb-2">
        <input placeholder="Visitor Name" className="border p-1 w-full mb-1" value={visitorName} onChange={e => setVisitorName(e.target.value)} />
        <input type="datetime-local" className="border p-1 w-full mb-1" value={validFrom} onChange={e => setValidFrom(e.target.value)} />
        <input type="datetime-local" className="border p-1 w-full mb-1" value={validUntil} onChange={e => setValidUntil(e.target.value)} />
      </div>
      <button className="bg-green-600 text-white px-4 py-2 rounded" onClick={createPass}>Generate Pass</button>
      {code && (
        <div className="mt-2 p-2 bg-gray-100 rounded border">
          Visitor Pass Code: <span className="font-mono">{code}</span>
        </div>
      )}
    </div>
  );
}
