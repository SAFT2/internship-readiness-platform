import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api, getErrorMessage } from "../lib/api";
import { setTokens } from "../lib/auth";
import { useSession } from "../lib/useSession";
import { useToast } from "../lib/useToast";

type Mode = "login" | "register";

export function AuthPage() {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { refreshSession } = useSession();
  const { pushToast } = useToast();

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const normalizedEmail = email.trim().toLowerCase();
    const normalizedFullName = fullName.trim();

    try {
      if (mode === "register") {
        await api.post("/auth/register", {
          email: normalizedEmail,
          full_name: normalizedFullName,
          password,
        });
      }

      const loginRes = await api.post("/auth/login", { email: normalizedEmail, password });
      setTokens(loginRes.data.access_token, loginRes.data.refresh_token);
      await refreshSession();
      pushToast("Signed in successfully", "success");
      navigate("/dashboard");
    } catch (err: unknown) {
      const message = getErrorMessage(err, "Authentication failed");
      setError(message);
      pushToast(message, "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page-section auth-section">
      <div className="container auth-shell">
        <section className="card auth-panel-modern auth-panel-centered">
          <div className="auth-panel-head">
            <p className="auth-kicker">InternReady AI</p>
            <h3>{mode === "login" ? "Welcome back" : "Create account"}</h3>
            <p>Use your backend auth endpoints directly.</p>
          </div>

          <div className="segmented auth-segmented">
            <button type="button" className={mode === "login" ? "seg active" : "seg"} onClick={() => setMode("login")}>
              Login
            </button>
            <button
              type="button"
              className={mode === "register" ? "seg active" : "seg"}
              onClick={() => setMode("register")}
            >
              Register
            </button>
          </div>

          <form onSubmit={onSubmit} className="form-grid auth-form-grid">
            <label>
              Email
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                type="email"
                placeholder="you@example.com"
              />
            </label>

            {mode === "register" && (
              <label>
                Full Name
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  minLength={2}
                  maxLength={255}
                  placeholder="Your full name"
                />
              </label>
            )}

            <label>
              Password
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                type="password"
                minLength={8}
                maxLength={128}
                placeholder="At least 8 characters"
              />
            </label>

            {error && <p className="error-text">{error}</p>}

            <button className="btn btn-primary wide auth-submit" type="submit" disabled={loading}>
              {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create and Sign In"}
            </button>
          </form>
        </section>
      </div>
    </section>
  );
}
