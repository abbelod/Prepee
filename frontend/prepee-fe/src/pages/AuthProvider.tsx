import { createContext, useContext, useEffect, useState } from "react";
import api from "../services/api"; // use your configured axios instance
import type { ReactNode } from "react";
type User = {
  id: number;
  username: string;
  email: string;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  setUser: (user: User | null) => void; // ✅ add setter
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("accessToken");
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        // Use your api instance so it automatically adds the Authorization header
        const response = await api.get("/auth/me/");
        setUser(response.data);
      } catch (error) {
        console.error("Failed to fetch user:", error);
        // If token is invalid, clear storage
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("user");
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []); // Still runs only on mount, but now setUser can be called later

  return (
    <AuthContext.Provider value={{ user, loading, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook for convenient access
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}