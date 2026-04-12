import { createContext } from "react";

export type SessionUser = {
  id: number;
  email: string;
  full_name: string;
};

export type SessionContextValue = {
  user: SessionUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  refreshSession: () => Promise<void>;
  signOut: () => void;
};

export const SessionContext = createContext<SessionContextValue | null>(null);
