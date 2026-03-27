import { createContext, useContext, useState, useCallback } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("jti_user");
    return stored ? JSON.parse(stored) : null;
  });

  const login = useCallback((userData, access, refresh) => {
    localStorage.setItem("jti_access", access);
    localStorage.setItem("jti_refresh", refresh);
    localStorage.setItem("jti_user", JSON.stringify(userData));
    setUser(userData);
  }, []);

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem("jti_refresh");
    const access = localStorage.getItem("jti_access");
    try {
      await fetch("/api/auth/logout/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${access}`,
        },
        body: JSON.stringify({ refresh }),
      });
    } catch {
      // proceed regardless
    }
    localStorage.removeItem("jti_access");
    localStorage.removeItem("jti_refresh");
    localStorage.removeItem("jti_user");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export function authHeaders() {
  const access = localStorage.getItem("jti_access");
  return access ? { Authorization: `Bearer ${access}` } : {};
}
