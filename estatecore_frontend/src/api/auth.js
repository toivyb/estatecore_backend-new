import api from "./client";
export async function login(email, password) {
  const { data } = await api.post("/api/login", { email, password });
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("role", data.role);
  localStorage.setItem("name", data.name);
  return data;
}
export function logout(){
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("name");
}
