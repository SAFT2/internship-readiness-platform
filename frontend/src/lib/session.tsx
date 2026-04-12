import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api } from "./api";
import { clearTokens, getAccessToken } from "./auth";
import { SessionContext } from "./sessionContext";
import type { SessionContextValue, SessionUser } from "./sessionContext";

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshSession() {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const res = await api.get<SessionUser>("/auth/me");
      setUser(res.data);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  function signOut() {
    clearTokens();
    setUser(null);
  }

  useEffect(() => {
    void refreshSession();
  }, []);

  const value = useMemo<SessionContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      refreshSession,
      signOut,
    }),
    [user, loading],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}
