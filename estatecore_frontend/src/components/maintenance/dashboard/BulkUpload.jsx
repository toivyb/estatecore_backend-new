export default function BulkUpload() {
  const handleUpload = async (e) => {
    const form = new FormData();
    form.append("file", e.target.files[0]);
    await fetch("/api/bulk-upload-users", { method: "POST", body: form });
    alert("Uploaded");
  };
  return <input type="file" accept=".csv" onChange={handleUpload} />;
}