import { Link } from "react-router-dom";

export function HeroSection() {
  return (
    <section className="hero-section">
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="container hero-content">
        <h1>
          Know If You&apos;re <span>Ready</span> for Your Dream Internship
        </h1>
        <p>
          Upload your resume and get an instant readiness score powered by NLP and machine learning. Discover
          skill gaps and get personalized recommendations to land your ideal role.
        </p>
        <div className="hero-actions">
          <Link to="/upload" className="btn btn-primary">
            <span className="btn-icon">^</span> Upload Resume
          </Link>
          <Link to="/dashboard" className="btn btn-outline">
            View Demo Dashboard {"->"}
          </Link>
        </div>
        <div className="hero-stats">
          <div>
            <strong>200+</strong>
            <span>Resumes Analyzed</span>
          </div>
          <div>
            <strong>95%</strong>
            <span>Accuracy Rate</span>
          </div>
          <div>
            <strong>3s</strong>
            <span>Avg Processing</span>
          </div>
        </div>
      </div>
    </section>
  );
}
