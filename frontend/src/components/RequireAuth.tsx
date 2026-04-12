import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useSession } from "../lib/useSession";

export function RequireAuth({ children }: { children: ReactNode }) {
  const location = useLocation();
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

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace state={{ from: location.pathname }} />;
  }

  return <>{children}</>;
}
