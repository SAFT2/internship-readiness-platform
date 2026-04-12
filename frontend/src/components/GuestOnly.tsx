import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useSession } from "../lib/useSession";

export function GuestOnly({ children }: { children: ReactNode }) {
  const { loading, isAuthenticated } = useSession();

  if (loading) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="muted-text">Loading your session...</p>
        </div>
      </section>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
