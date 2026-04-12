import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useSession } from "../lib/useSession";

const links = [
  { to: "/upload", label: "Assess Resume" },
  { to: "/dashboard", label: "Readiness Dashboard" },
  { to: "/history", label: "History" },
  { to: "/profile", label: "Resources" },
];

export function NavBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, signOut } = useSession();
  const [mobileOpen, setMobileOpen] = useState(false);

  function onSignOut() {
    signOut();
    setMobileOpen(false);
    navigate("/auth");
  }

  return (
    <header className="navbar glass">
      <div className="container nav-inner">
        <Link to="/" className="logo">
          InternReady AI
        </Link>

        <nav className="topnav">
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={location.pathname === link.to ? "nav-link active" : "nav-link"}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="nav-actions">
          {!isAuthenticated ? (
            <Link to="/auth" className="btn btn-ghost" onClick={() => setMobileOpen(false)}>
              Sign In
            </Link>
          ) : (
            <button className="btn btn-ghost" onClick={onSignOut}>
              Log Out
            </button>
          )}
          <Link to="/upload" className="btn btn-primary">
            Get Started
          </Link>
        </div>

        <button
          type="button"
          className="mobile-nav-toggle"
          aria-label="Toggle navigation"
          aria-expanded={mobileOpen}
          onClick={() => setMobileOpen((prev) => !prev)}
        >
          {mobileOpen ? "Close" : "Menu"}
        </button>
      </div>

      <div className={mobileOpen ? "container mobile-nav open" : "container mobile-nav"}>
        <nav className="mobile-nav-links">
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={location.pathname === link.to ? "nav-link active" : "nav-link"}
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="mobile-nav-actions">
          {!isAuthenticated ? (
            <Link to="/auth" className="btn btn-ghost wide" onClick={() => setMobileOpen(false)}>
              Sign In
            </Link>
          ) : (
            <button type="button" className="btn btn-ghost wide" onClick={onSignOut}>
              Log Out
            </button>
          )}
          <Link to="/upload" className="btn btn-primary wide" onClick={() => setMobileOpen(false)}>
            Get Started
          </Link>
        </div>
      </div>
    </header>
  );
}
