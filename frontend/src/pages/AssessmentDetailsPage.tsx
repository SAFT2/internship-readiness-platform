import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { Link, useParams } from "react-router-dom";
import { Footer } from "../components/Footer";
import { api, getErrorMessage } from "../lib/api";

type Recommendation = {
  action?: string;
  reason?: string;
  priority?: string;
};

type AssessmentDetails = {
  id: number;
  target_role: string;
  overall_score: number;
  readiness_level: string;
  source_type: string;
  missing_required_skills: string[];
  recommendations: Recommendation[];
  score_breakdown: Record<string, number>;
  created_at: string;
};

export function AssessmentDetailsPage() {
  const { id } = useParams();
  const [details, setDetails] = useState<AssessmentDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const res = await api.get<AssessmentDetails>(`/assessments/${id}`);
        setDetails(res.data);
      } catch (err: unknown) {
        setError(getErrorMessage(err, "Unable to load assessment"));
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [id]);

  return (
    <>
      <section className="page-section">
        <div className="container">
          <div className="dashboard-header">
            <div>
              <h1>Assessment Result</h1>
              <p>Detailed view for assessment #{id}</p>
            </div>
            <Link to="/history" className="btn btn-outline">
              Back to History
            </Link>
          </div>

          {loading && <p className="muted-text">Loading assessment...</p>}
          {error && <p className="error-text">{error}</p>}

          {details && (
            <>
              {(() => {
                const scorePercent = Math.max(0, Math.min(100, details.overall_score));
                return (
              <article className="card dashboard-score-hero">
                <div className="score-ring-wrap">
                  <div
                    className="score-ring"
                    style={{ "--score": `${scorePercent}%` } as CSSProperties}
                    aria-label={`Assessment score ${scorePercent.toFixed(2)} percent`}
                  >
                    <strong>{details.overall_score.toFixed(2)}</strong>
                    <span>SCORE</span>
                  </div>
                </div>
                <div className="score-copy">
                  <span className="status-pill">{details.readiness_level}</span>
                  <h3>{details.target_role}</h3>
                  <p>
                    Source: {details.source_type} | Assessed on {new Date(details.created_at).toLocaleString()}
                  </p>
                </div>
              </article>
                );
              })()}

              <div className="dashboard-skill-grid">
                <article className="card skill-card">
                  <h4>Missing Required Skills</h4>
                  <div className="chip-grid">
                    {(details.missing_required_skills || []).slice(0, 8).map((skill) => (
                      <span key={skill} className="chip chip-missing">
                        {skill}
                      </span>
                    ))}
                    {details.missing_required_skills.length === 0 && (
                      <p className="muted-text">No missing required skills detected.</p>
                    )}
                  </div>
                </article>

                <article className="card skill-card">
                  <h4>Score Breakdown</h4>
                  <div className="detail-kv-list">
                    {Object.entries(details.score_breakdown || {}).map(([key, value]) => (
                      <div key={key} className="detail-kv-row">
                        <span>{key}</span>
                        <strong>{Math.round(Number(value))}</strong>
                      </div>
                    ))}
                  </div>
                </article>
              </div>

              <section className="recommendation-section">
                <h2>Recommendations</h2>
                {details.recommendations.length === 0 && <p className="muted-text">No recommendations available.</p>}
                {details.recommendations.map((rec, index) => (
                  <article key={`${rec.action ?? "rec"}-${index}`} className="card recommendation-card medium">
                    <div>
                      <span className="priority-badge medium">{rec.priority ?? "Suggestion"}</span>
                      <h4>{rec.action ?? "Action item"}</h4>
                      <p>{rec.reason ?? "No additional reason provided."}</p>
                    </div>
                  </article>
                ))}
              </section>
            </>
          )}
        </div>
      </section>
      <Footer />
    </>
  );
}
