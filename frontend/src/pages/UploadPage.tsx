import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { BarChart3, Shield, Upload, WandSparkles } from "lucide-react";
import { api, getErrorMessage } from "../lib/api";
import { Footer } from "../components/Footer";
import { useToast } from "../lib/useToast";

type UploadResult = {
  overall_score: number;
  readiness_level: string;
};

type RoleCatalogResponse = {
  roles: string[];
};

type RoleDetails = {
  total_postings: number;
  remote_percentage: number;
};

export function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [role, setRole] = useState("");
  const [roles, setRoles] = useState<string[]>([]);
  const [roleDetails, setRoleDetails] = useState<RoleDetails | null>(null);
  const [rolesLoading, setRolesLoading] = useState(false);
  const [roleDetailsLoading, setRoleDetailsLoading] = useState(false);
  const [roleDetailsError, setRoleDetailsError] = useState("");
  const [result, setResult] = useState<UploadResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [profileAssessing, setProfileAssessing] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { pushToast } = useToast();

  useEffect(() => {
    async function loadRoles() {
      setRolesLoading(true);
      setRoleDetailsError("");
      try {
        const res = await api.get<RoleCatalogResponse>("/assessments/roles");
        const fetchedRoles = res.data.roles || [];
        const uniqueRoles = Array.from(new Set(fetchedRoles.filter(Boolean)));
        setRoles(uniqueRoles);

        if (uniqueRoles.length > 0) {
          setRole((prev) => prev || uniqueRoles[0]);
        }
      } catch (err: unknown) {
        setRoleDetailsError(getErrorMessage(err, "Unable to load roles"));
      } finally {
        setRolesLoading(false);
      }
    }

    void loadRoles();
  }, []);

  useEffect(() => {
    if (!role) {
      setRoleDetails(null);
      return;
    }

    async function loadRoleDetails() {
      setRoleDetailsLoading(true);
      setRoleDetailsError("");
      try {
        const res = await api.get<RoleDetails>(`/assessments/roles/${encodeURIComponent(role)}`);
        setRoleDetails(res.data);
      } catch (err: unknown) {
        setRoleDetails(null);
        setRoleDetailsError(getErrorMessage(err, "Unable to load role details"));
      } finally {
        setRoleDetailsLoading(false);
      }
    }

    void loadRoleDetails();
  }, [role]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;

    setError("");
    setLoading(true);

    try {
      const form = new FormData();
      form.append("resume", file);
      form.append("role", role);

      const res = await api.post("/assessments/from-resume", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setResult(res.data);
      pushToast("Resume analyzed successfully", "success");
    } catch (err: unknown) {
      const msg = getErrorMessage(err, "Upload failed");
      setError(msg);
      pushToast(msg, "error");
    } finally {
      setLoading(false);
    }
  }

  async function assessFromProfile() {
    setProfileAssessing(true);
    setError("");
    try {
      const res = await api.post("/assessments/from-profile", {
        role,
      });
      pushToast("Profile assessment created", "success");
      navigate(`/assessments/${res.data.id}`);
    } catch (err: unknown) {
      const msg = getErrorMessage(err, "Profile assessment failed");
      setError(msg);
      pushToast(msg, "error");
    } finally {
      setProfileAssessing(false);
    }
  }

  return (
    <>
      <section className="page-section">
        <div className="container upload-wrap">
          <div className="section-heading center">
            <h1>
              Perfect Your <span>InternReady AI</span> Application
            </h1>
            <p>
              Our AI-driven analysis scans your resume against thousands of successful engineering placements to give
              you an editorial-grade readiness score.
            </p>
          </div>

          <form onSubmit={onSubmit} className="upload-grid upload-grid-polished">
            <div className="card soft-card upload-card">
              <h3>Upload Resume</h3>
              <div
                className={dragging ? "dropzone active" : "dropzone"}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragging(false);
                  const dropped = e.dataTransfer.files?.[0] ?? null;
                  if (dropped && dropped.type === "application/pdf") {
                    setFile(dropped);
                  }
                }}
              >
                <div className="drop-icon" aria-hidden="true">
                  <Upload size={28} />
                </div>
                <p className="drop-title">Drag and drop your PDF</p>
                <p className="drop-sub">Max file size 5MB. PDF format only.</p>
                <label className="browse-link">
                  Or browse files
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    required
                  />
                </label>
              </div>

              {file && <p className="file-pill">Selected: {file.name}</p>}

              {result && (
                <div className="result-card">
                  <h4>Latest Result</h4>
                  <p>
                    Score <strong>{result.overall_score}</strong> | Level <strong>{result.readiness_level}</strong>
                  </p>
                  <button className="btn btn-outline" type="button" onClick={() => navigate("/dashboard")}>
                    Open Dashboard
                  </button>
                </div>
              )}
            </div>

            <div className="stack-gap upload-side">
              <label className="role-label">
                Target Internship Role
                <select
                  className="role-select"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  required
                  disabled={rolesLoading || roles.length === 0}
                >
                  {roles.length === 0 && <option value="">No roles available</option>}
                  {roles.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>

              {rolesLoading && <p className="muted-text">Loading role catalog...</p>}
              {roleDetailsError && <p className="error-text">{roleDetailsError}</p>}

              {roleDetails && (
                <p className="role-meta">
                  Based on {roleDetails.total_postings} postings | {Math.round(roleDetails.remote_percentage)}% remote
                </p>
              )}

              {roleDetailsLoading && <p className="muted-text">Loading role details...</p>}

              <ul className="upload-benefits">
                <li>
                  <Shield size={18} />
                  Secure AI Processing
                </li>
                <li>
                  <BarChart3 size={18} />
                  Industry Benchmark Comparison
                </li>
              </ul>

              <button type="submit" className="btn btn-primary wide upload-analyze" disabled={loading || !file || !role}>
                {loading ? "Analyzing Resume..." : (
                  <>
                    <WandSparkles size={16} /> Analyze Resume
                  </>
                )}
              </button>

              <button type="button" className="btn btn-outline wide" onClick={assessFromProfile} disabled={profileAssessing}>
                {profileAssessing ? "Assessing Profile..." : "Use Profile Instead"}
              </button>

              {error && <p className="error-text">{error}</p>}

              <div className="tip-box">
                <h4>Pro Tip</h4>
                <p>
                  Include measurable outcomes like "Improved performance by 20%" to increase your readiness score.
                </p>
              </div>
            </div>
          </form>
        </div>
      </section>
      <Footer />
    </>
  );
}
