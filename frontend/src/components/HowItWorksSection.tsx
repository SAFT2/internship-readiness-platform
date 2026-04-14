const steps = [
  { title: "Upload Resume", description: "Upload your resume in PDF format." },
  { title: "AI Analysis", description: "NLP extracts your skills and experience profile." },
  { title: "Score and Gaps", description: "Model computes readiness and identifies missing requirements." },
  { title: "Recommendations", description: "Receive personalized pathways to improve quickly." },
];

export function HowItWorksSection() {
  return (
    <section className="section section-tinted">
      <div className="container">
        <div className="section-heading">
          <h2>Simple 4-Step Process</h2>
          <p>From resume upload to actionable insights in seconds.</p>
        </div>
        <div className="step-grid">
          {steps.map((step, index) => (
            <article key={step.title} className="step-card">
              <span className="step-badge">{index + 1}</span>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
