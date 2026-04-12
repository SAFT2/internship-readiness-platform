import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Footer } from "../components/Footer";
import { api, getErrorMessage } from "../lib/api";
import { resourceLinkForAction } from "../lib/resources";
import { useToast } from "../lib/useToast";

type Summary = {
  latest_score: number | null;
  readiness_level: string | null;
  total_assessments: number;
  target_role?: string | null;
  missing_skills_top5?: string[];
  recommendations_top3?: string[];
};

type TrendPoint = {
  label: string;
  score: number;
};

type Benchmark = {
  compared_role: string;
  latest_score: number;
  target_ready_score: number;
  score_gap_to_ready: number;
  required_skills_total: number;
  missing_required_skills_count: number;
  required_skill_coverage_pct: number;
  market_new_grad_friendly_percentage: number | null;
  market_remote_percentage: number | null;
};

type LatestAssessment = {
  target_role: string;
  score_breakdown: Record<string, number>;
  missing_required_skills: string[];
};

type ProfileOut = {
  skills: string[];
};

type RoleDetails = {
  total_postings: number;
  top_required_skills: string[];
  remote_percentage: number;
};

export function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [benchmark, setBenchmark] = useState<Benchmark | null>(null);
  const [latestAssessment, setLatestAssessment] = useState<LatestAssessment | null>(null);
  const [profileSkills, setProfileSkills] = useState<string[]>([]);
  const [roleDetails, setRoleDetails] = useState<RoleDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showOnboardingHint, setShowOnboardingHint] = useState(false);
  const { pushToast } = useToast();

  useEffect(() => {
    const dismissed = window.localStorage.getItem("dashboard-hints-dismissed");
    setShowOnboardingHint(dismissed !== "true");
  }, []);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [summaryRes, trendRes, latestRes, profileRes] = await Promise.all([
          api.get("/dashboard/summary"),
          api.get("/dashboard/trend", { params: { points: 10 } }),
          api.get<LatestAssessment | null>("/assessments/latest"),
          api.get<ProfileOut>("/profile/me"),
        ]);

        setSummary(summaryRes.data);
        setTrend(trendRes.data.points || []);
        setLatestAssessment(latestRes.data);
        setProfileSkills(profileRes.data?.skills || []);

        const targetRole = summaryRes.data?.target_role || latestRes.data?.target_role;
        if (targetRole) {
          const [benchmarkRes, roleDetailsRes] = await Promise.all([
            api.get("/assessments/benchmark", {
              params: { role_name: targetRole },
            }),
            api.get<RoleDetails>(`/assessments/roles/${encodeURIComponent(targetRole)}`),
          ]);
          setBenchmark(benchmarkRes.data);
          setRoleDetails(roleDetailsRes.data);
        } else {
          setBenchmark(null);
          setRoleDetails(null);
        }
      } catch (err: unknown) {
        const msg = getErrorMessage(err, "Unable to load dashboard");
        setError(msg);
        pushToast(msg, "error");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [pushToast]);

  const latestScore = typeof summary?.latest_score === "number" ? summary.latest_score : null;
  const scorePercent = Math.max(0, Math.min(100, latestScore ?? 0));
  const scoreBreakdown = latestAssessment?.score_breakdown || {};

  const technicalScorePct = Math.max(0, Math.min(100, Math.round((Number(scoreBreakdown.skills_total || 0) / 50) * 100)));
  const projectScorePct = Math.max(0, Math.min(100, Math.round((Number(scoreBreakdown.projects || 0) / 30) * 100)));
  const experienceScorePct = Math.max(0, Math.min(100, Math.round((Number(scoreBreakdown.experience || 0) / 20) * 100)));

  const missingSkills =
    summary?.missing_skills_top5?.length
      ? summary.missing_skills_top5
      : latestAssessment?.missing_required_skills || [];

  const missingSkillSet = new Set(missingSkills.map((item) => item.toLowerCase()));
  const matchedSkills = profileSkills.filter((skill) => !missingSkillSet.has(skill.toLowerCase())).slice(0, 6);
  const roleHighlights = (roleDetails?.top_required_skills || []).slice(0, 5);
  const snapshotCoveredCount = roleHighlights.filter((skill) => !missingSkillSet.has(skill.toLowerCase())).length;
  const snapshotCoveragePct = roleHighlights.length
    ? Math.round((snapshotCoveredCount / roleHighlights.length) * 100)
    : Math.max(0, Math.min(100, Math.round(benchmark?.required_skill_coverage_pct ?? 0)));

  function capabilityMessage(category: "technical" | "projects" | "experience", pct: number): string {
    if (category === "technical") {
      if (pct >= 75) return "Strong alignment with required technical expectations.";
      if (pct >= 45) return "Core technical grounding is visible with room to sharpen depth.";
      return "Build stronger technical depth through role-aligned practice projects.";
    }
    if (category === "projects") {
      if (pct >= 75) return "Project portfolio is strong and signals real implementation ability.";
      if (pct >= 45) return "Projects show promise but need broader impact and polish.";
      return "Add more end-to-end projects to demonstrate readiness.";
    }
    if (pct >= 75) return "Experience signals good market readiness for intern opportunities.";
    if (pct >= 45) return "Some practical exposure exists, but impact can be improved.";
    return "Hands-on experience is limited and should be strengthened.";
  }

  async function downloadReport() {
    try {
      const response = await api.get("/dashboard/report.pdf", {
        responseType: "blob",
      });

      const contentType = String(response.headers["content-type"] || "").toLowerCase();
      const disposition = String(response.headers["content-disposition"] || "");
      const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
      const fallbackFilename = contentType.includes("application/pdf")
        ? "internready-report.pdf"
        : "internready-report.txt";
      const filename = filenameMatch?.[1] || fallbackFilename;

      const blobUrl = URL.createObjectURL(response.data);
      const anchor = document.createElement("a");
      anchor.href = blobUrl;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(blobUrl);

      if (contentType.includes("application/pdf")) {
        pushToast("PDF report downloaded", "success");
      } else {
        pushToast("Fallback report downloaded", "info");
      }
    } catch (err: unknown) {
      pushToast(getErrorMessage(err, "Unable to download report"), "error");
    }
  }

  function dismissOnboardingHint() {
    window.localStorage.setItem("dashboard-hints-dismissed", "true");
    setShowOnboardingHint(false);
  }

  return (
    <>
      <section className="page-section">
        <div className="container">
          {showOnboardingHint && (
            <div className="card soft-card hint-banner">
              <p>
                Tip: Start from <strong>Assess Resume</strong>, then use <strong>Download Report</strong> after at least one completed assessment.
              </p>
              <button type="button" className="btn btn-outline" onClick={dismissOnboardingHint}>
                Got it
              </button>
            </div>
          )}

          <div className="dashboard-header">
            <div>
              <h1>InternReady AI Results</h1>
              <p>
                Analysis for {summary?.target_role ?? "your latest target internship role"}
              </p>
            </div>
            <button
              className="btn btn-outline"
              type="button"
              onClick={downloadReport}
              disabled={loading || !summary}
              title="Download a backend-generated PDF summary report"
            >
              Download Report
            </button>
          </div>

          {loading && <p className="muted-text">Loading dashboard metrics...</p>}

          {error && <p className="error-text">{error}</p>}

          {!loading && !summary?.latest_score && !error && (
            <div className="card soft-card">
              <h3>No assessment data yet</h3>
              <p className="muted-text">Create your first assessment from upload or profile to populate this dashboard.</p>
            </div>
          )}

          <article className="card dashboard-score-hero">
            <div className="score-ring-wrap">
              <div
                className="score-ring"
                style={{ "--score": `${scorePercent}%` } as CSSProperties}
                aria-label={`Readiness score ${scorePercent.toFixed(2)} percent`}
              >
                <strong>{latestScore === null ? "-" : latestScore.toFixed(2)}</strong>
                <span>SCORE</span>
              </div>
            </div>
            <div className="score-copy">
              <span className="status-pill">{summary?.readiness_level ?? "In Progress"}</span>
              <h3>Your profile is competitive for internship hiring benchmarks.</h3>
              <p>
                Keep improving role-specific skills to increase match confidence and move toward top-tier readiness.
              </p>
            </div>
          </article>

          <article className="card primary-card role-snapshot-card">
            <div className="snapshot-head">
              <div>
                <h3>Role Snapshot</h3>
                <p>
                  {roleDetails
                    ? `Top market requirements based on ${roleDetails.total_postings} postings (${Math.round(roleDetails.remote_percentage)}% remote).`
                    : "Top market requirements for your selected internship role."}
                </p>
              </div>
              <div className="snapshot-coverage-wrap">
                <span className="snapshot-coverage-label">Coverage</span>
                <strong className="snapshot-coverage-value">{snapshotCoveragePct}%</strong>
              </div>
            </div>

            <div className="snapshot-coverage-bar" role="progressbar" aria-valuenow={snapshotCoveragePct} aria-valuemin={0} aria-valuemax={100}>
              <div className="snapshot-coverage-fill" style={{ width: `${snapshotCoveragePct}%` }} />
            </div>

            <div className="snapshot-list">
              {latestAssessment && roleHighlights.length > 0 ? (
                roleHighlights.map((skill) => {
                  const covered = !missingSkillSet.has(skill.toLowerCase());
                  return (
                    <div key={skill} className="snapshot-skill-row">
                      <span className="snapshot-skill-name">{skill}</span>
                      <strong className={covered ? "snapshot-status snapshot-status-covered" : "snapshot-status snapshot-status-missing"}>
                        {covered ? "Covered" : "Missing"}
                      </strong>
                    </div>
                  );
                })
              ) : (
                <p className="snapshot-empty">{latestAssessment ? "Role-specific market data is still loading." : "Role-specific market data will appear after your first assessment."}</p>
              )}
            </div>
          </article>

          {latestAssessment ? (
            <>
              <div className="dashboard-capability-grid">
                <article className="card capability-card">
                  <div className="capability-head">
                    <span className="capability-icon">{`<>`}</span>
                    <strong>{technicalScorePct}%</strong>
                  </div>
                  <h4>Technical Skills</h4>
                  <p>{capabilityMessage("technical", technicalScorePct)}</p>
                </article>
                <article className="card capability-card">
                  <div className="capability-head">
                    <span className="capability-icon">[]</span>
                    <strong>{projectScorePct}%</strong>
                  </div>
                  <h4>Projects</h4>
                  <p>{capabilityMessage("projects", projectScorePct)}</p>
                </article>
                <article className="card capability-card">
                  <div className="capability-head">
                    <span className="capability-icon">::</span>
                    <strong>{experienceScorePct}%</strong>
                  </div>
                  <h4>Experience</h4>
                  <p>{capabilityMessage("experience", experienceScorePct)}</p>
                </article>
              </div>

              <div className="dashboard-skill-grid">
                <article className="card skill-card">
                  <h4>Missing Required Skills</h4>
                  <div className="chip-grid">
                    {missingSkills.map((skill) => (
                      <span key={skill} className="chip chip-missing">
                        {skill}
                      </span>
                    ))}
                    {missingSkills.length === 0 && <p className="muted-text">No major missing required skills detected.</p>}
                  </div>
                </article>
                <article className="card skill-card">
                  <h4>Matched Skills</h4>
                  <div className="chip-grid">
                    {matchedSkills.map((skill) => (
                      <span key={skill} className="chip chip-match">
                        {skill}
                      </span>
                    ))}
                    {matchedSkills.length === 0 && <p className="muted-text">Matched skills will appear after profile enrichment.</p>}
                  </div>
                </article>
              </div>
            </>
          ) : (
            <div className="card soft-card">
              <h3>Detailed capability sections are not available yet</h3>
              <p className="muted-text">Run an assessment to unlock role snapshot, capability scoring, and skill matching insights.</p>
            </div>
          )}

          <section className="recommendation-section">
            <h2>Prioritized Recommendations</h2>
            {(summary?.recommendations_top3 || []).map((action, index) => (
              <article key={action} className="card recommendation-card medium">
                <div>
                  <span className={`priority-badge ${index === 0 ? "high" : "medium"}`}>
                    {index === 0 ? "High Priority" : "Medium Priority"}
                  </span>
                  <h4>{action}</h4>
                  <p>Mapped learning resources based on your current skill gap analysis.</p>
                </div>
                <a href={resourceLinkForAction(action)} target="_blank" rel="noreferrer">
                  Open Learning Path {"->"}
                </a>
              </article>
            ))}
            {!loading && (summary?.recommendations_top3 || []).length === 0 && (
              <div className="card soft-card">
                <p className="muted-text">No recommendations yet. Complete an assessment to generate an action plan.</p>
              </div>
            )}
          </section>

          {benchmark && (
            <section className="card soft-card benchmark-card">
              <h3>Benchmark View</h3>
              <div className="benchmark-grid">
                <div className="benchmark-item">
                  <span>Compared Role</span>
                  <strong>{benchmark.compared_role}</strong>
                </div>
                <div className="benchmark-item">
                  <span>Ready Score Target</span>
                  <strong>{benchmark.target_ready_score}</strong>
                </div>
                <div className="benchmark-item">
                  <span>Score Gap to Ready</span>
                  <strong>{benchmark.score_gap_to_ready}</strong>
                </div>
                <div className="benchmark-item">
                  <span>Required Skill Coverage</span>
                  <strong>{benchmark.required_skill_coverage_pct}%</strong>
                </div>
              </div>
            </section>
          )}

          <div className="chart-box card soft-card">
            <h3>Trend</h3>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trend}>
                <XAxis dataKey="label" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="score" stroke="#2459c8" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>
      <Footer />
    </>
  );
}
