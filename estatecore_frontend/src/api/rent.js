import api from "./client";
export async function listRent(){
  const { data } = await api.get("/api/rent/list");
  return data.items;
}
export async function createRent(payload){
  const { data } = await api.post("/api/rent/create", payload);
  return data.id;
}
export function receiptUrl(id){
  const base = import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_BASE_URL;
  return `${base}/api/pdf/rent-receipt/${id}`;
}
