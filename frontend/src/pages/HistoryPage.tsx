import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Footer } from "../components/Footer";
import { api, getErrorMessage } from "../lib/api";
import { resourceLinkForAction } from "../lib/resources";

type HistoryItem = {
  id: number;
  created_at: string;
  target_role: string;
  overall_score: number;
  readiness_level: string;
  source_type: string;
};

type HistoryPageResponse = {
  items: HistoryItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
};

type RoleCatalogResponse = {
  roles: string[];
};

type LatestAssessmentResponse = {
  recommendations?: Array<{ action?: string }>;
};

const PAGE_SIZE = 8;

export function HistoryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [rows, setRows] = useState<HistoryItem[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [rolesLoading, setRolesLoading] = useState(false);
  const [rolesError, setRolesError] = useState("");
  const [roleFilter, setRoleFilter] = useState(searchParams.get("role") ?? "");
  const [sourceFilter, setSourceFilter] = useState<"all" | "resume" | "profile">(
    (searchParams.get("source") as "all" | "resume" | "profile") || "all",
  );
  const [searchTerm, setSearchTerm] = useState(searchParams.get("q") ?? "");
  const [offset, setOffset] = useState(Number(searchParams.get("offset") || 0));
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [learningPathUrl, setLearningPathUrl] = useState<string | null>(null);

  useEffect(() => {
    async function loadRoles() {
      try {
        setRolesLoading(true);
        setRolesError("");
        const res = await api.get<RoleCatalogResponse>("/assessments/roles");
        setRoles(res.data.roles || []);
      } catch {
        setRoles([]);
        setRolesError("Role catalog unavailable.");
      } finally {
        setRolesLoading(false);
      }
    }

    void loadRoles();
  }, []);

  useEffect(() => {
    async function loadLearningPath() {
      try {
        const res = await api.get<LatestAssessmentResponse | null>("/assessments/latest");
        const action = res.data?.recommendations?.find((item) => item?.action?.trim())?.action?.trim();
        setLearningPathUrl(action ? resourceLinkForAction(action) : null);
      } catch {
        setLearningPathUrl(null);
      }
    }

    void loadLearningPath();
  }, []);

  useEffect(() => {
    const next = new URLSearchParams();
    if (roleFilter) next.set("role", roleFilter);
    if (sourceFilter !== "all") next.set("source", sourceFilter);
    if (searchTerm.trim()) next.set("q", searchTerm.trim());
    if (offset > 0) next.set("offset", String(offset));
    setSearchParams(next, { replace: true });
  }, [offset, roleFilter, searchTerm, setSearchParams, sourceFilter]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const res = await api.get<HistoryPageResponse>("/assessments/history/query", {
          params: {
            limit: PAGE_SIZE,
            offset,
            role_name: roleFilter || undefined,
            source_type: sourceFilter === "all" ? undefined : sourceFilter,
          },
        });
        setRows(res.data.items || []);
        setTotal(res.data.total || 0);
        setHasMore(Boolean(res.data.has_more));
      } catch (err: unknown) {
        setError(getErrorMessage(err, "Unable to load history"));
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [offset, roleFilter, sourceFilter]);

  const filteredRows = rows.filter((row) =>
    row.target_role.toLowerCase().includes(searchTerm.trim().toLowerCase()),
  );

  const avgScore = filteredRows.length
    ? Math.round(filteredRows.reduce((acc, row) => acc + row.overall_score, 0) / filteredRows.length)
    : 0;

  function readinessBadge(level: string): string {
    const value = level.toLowerCase();
    if (value.includes("ready")) return "badge-ready";
    if (value.includes("polish")) return "badge-polish";
    return "badge-neutral";
  }

  return (
    <>
      <section className="page-section">
        <div className="container">
          <div className="history-heading">
            <h1>Assessment History</h1>
            <p>Track your progress and revisit AI-powered insights from previous resume scans.</p>
          </div>

          <div className="history-stack">
            <div className="card soft-card history-insight-card">
              <span className="tag">Latest Insight</span>
              <h2>Your internship readiness improved in recent assessments</h2>
              <p>Based on your recent submissions, technical communication has become more precise.</p>
              <Link to="/upload" className="btn btn-primary">
                Resume Assessment {"->"}
              </Link>
            </div>
            <div className="card primary-card history-avg-card">
              <div className="avg-ring">{avgScore}</div>
              <h3>Avg. Readiness Score</h3>
              <p>Steady growth across your latest applications</p>
            </div>
          </div>

          {error && <p className="error-text">{error}</p>}

          <div className="table-wrap card soft-card">
            <div className="history-filter-row">
              <div className="history-filter-group">
                <label>
                  Role Filter
                  <select
                    disabled={rolesLoading}
                    value={roleFilter}
                    onChange={(e) => {
                      setRoleFilter(e.target.value);
                      setOffset(0);
                    }}
                  >
                    <option value="">All roles</option>
                    {roles.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Source Filter
                  <select
                    value={sourceFilter}
                    onChange={(e) => {
                      setSourceFilter(e.target.value as "all" | "resume" | "profile");
                      setOffset(0);
                    }}
                  >
                    <option value="all">All</option>
                    <option value="resume">Resume</option>
                    <option value="profile">Profile</option>
                  </select>
                </label>
              </div>
              <p className="history-meta">
                Showing {offset + 1}-{Math.min(offset + PAGE_SIZE, total)} of {total}
              </p>
            </div>

            {rolesError && <p className="muted-text">{rolesError}</p>}

            <div className="table-headline">
              <h3>Recent Activity</h3>
              <input
                className="table-search"
                placeholder="Search current page roles..."
                value={searchTerm}
                disabled={loading}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <table>
              <thead>
                <tr>
                  <th>Assessment Date</th>
                  <th>Target Role</th>
                  <th>Readiness Level</th>
                  <th>Score</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading && (
                  <tr>
                    <td className="table-empty" colSpan={5}>
                      Loading assessments...
                    </td>
                  </tr>
                )}
                {filteredRows.map((row) => (
                  <tr key={row.id}>
                    <td>{new Date(row.created_at).toLocaleDateString()}</td>
                    <td>
                      <span className="role-cell">{row.target_role}</span>
                    </td>
                    <td>
                      <span className={`level-badge ${readinessBadge(row.readiness_level)}`}>{row.readiness_level}</span>
                    </td>
                    <td>
                      <strong className="score-value">{row.overall_score}</strong>
                    </td>
                    <td>
                      <Link to={`/assessments/${row.id}`} className="result-link">
                        Open Result {"->"}
                      </Link>
                    </td>
                  </tr>
                ))}
                {!loading && filteredRows.length === 0 && (
                  <tr>
                    <td className="table-empty" colSpan={5}>
                      {total === 0 ? "No assessments yet. Run your first assessment to populate history." : "No assessments match your current filters."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>

            <div className="pagination-row">
              <button
                type="button"
                className="btn btn-outline"
                disabled={offset === 0 || loading}
                onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_SIZE))}
              >
                Previous
              </button>
              <span className="pagination-label">Page {Math.floor(offset / PAGE_SIZE) + 1}</span>
              <button
                type="button"
                className="btn btn-outline"
                disabled={!hasMore || loading}
                onClick={() => setOffset((prev) => prev + PAGE_SIZE)}
              >
                Next
              </button>
            </div>
          </div>

          <div className="cta-banner">
            <div>
              <h2>Ready to see where you stand today?</h2>
              <p>Our AI algorithms are continuously updated with the latest hiring benchmarks.</p>
              <div className="cta-actions">
                <Link to="/upload" className="btn btn-secondary">
                  New Assessment
                </Link>
                {learningPathUrl ? (
                  <a className="btn btn-outline-light" href={learningPathUrl} target="_blank" rel="noreferrer">
                    View Learning Path
                  </a>
                ) : (
                  <Link className="btn btn-outline-light" to="/dashboard">
                    Open Dashboard
                  </Link>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
      <Footer />
    </>
  );
}
