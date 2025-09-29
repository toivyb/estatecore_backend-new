import { createContext, useContext, useEffect, useState } from 'react';
import api from '../api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [me, setMe] = useState(null);

  const fetchUser = async () => {
    try {
      const res = await api.get('/me');
      setMe(res.data);
    } catch {
      setMe(null);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const login = async (email, password) => {
    await api.post('/login', { email, password });
    fetchUser();
  };

  const logout = async () => {
    await api.post('/logout');
    setMe(null);
  };

  return (
    <AuthContext.Provider value={{ me, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
