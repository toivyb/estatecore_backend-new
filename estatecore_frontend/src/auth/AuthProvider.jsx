import { createContext, useContext, useEffect, useMemo, useState } from "react";
import client from "../api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("access_token"));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token && !user) {
      setLoading(true);
      client.get("/api/auth/me")
        .then(r => {
          setUser(r.data);
          localStorage.setItem("user", JSON.stringify(r.data));
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [token, user]);

  const login = (access_token, u) => {
    localStorage.setItem("access_token", access_token);
    setToken(access_token);
    if (u) {
      localStorage.setItem("user", JSON.stringify(u));
      setUser(u);
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setToken(null); setUser(null);
  };

  const hasRole = (...rs) => {
    const roles = user?.roles || [];
    return rs.some(r => roles.includes(r));
  };

  const value = useMemo(() => ({ token, user, loading, login, logout, hasRole }), [token, user, loading]);
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
