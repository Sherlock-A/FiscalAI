"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface AuthState {
  isReady: boolean;
  logout: () => void;
}

export const AuthContext = createContext<AuthState>({ isReady: false, logout: () => {} });

export function useAuth() {
  return useContext(AuthContext);
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [isReady, setIsReady] = useState(false);
  const router = useRouter();
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  useEffect(() => {
    const existing = localStorage.getItem("access_token");
    if (existing) {
      setIsReady(true);
      return;
    }

    fetch(`${API_BASE}/api/v1/auth/demo-token`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.access_token) {
          localStorage.setItem("access_token", data.access_token);
          setIsReady(true);
        }
      })
      .catch(() => {});
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    queryClient.clear();
    setIsReady(false);
    router.push("/");
  }, [queryClient, router]);

  return (
    <AuthContext.Provider value={{ isReady, logout }}>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </AuthContext.Provider>
  );
}
