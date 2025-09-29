import { useState } from "react";

export default function RentUpload() {
  const [file, setFile] = useState(null);

  const handleUpload = async () => {
    if (!file) return;
    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("file", file);
    await fetch("/api/rent/upload", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });
    alert("Uploaded");
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Bulk Rent Upload</h2>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button
        onClick={handleUpload}
        className="ml-2 px-4 py-2 bg-blue-600 text-white"
      >
        Upload
      </button>
    </div>
  );
}
