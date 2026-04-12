const features = [
  {
    title: "AI Resume Parsing",
    description: "NLP extracts skills, education, projects, and experience with recruiter-style precision.",
  },
  {
    title: "Market Benchmarking",
    description: "Compare your profile against current internship requirements and hiring trends.",
  },
  {
    title: "Actionable Feedback",
    description: "Get practical recommendations to increase your readiness score quickly.",
  },
];

export function FeaturesSection() {
  return (
    <section className="section section-white">
      <div className="container">
        <div className="section-heading">
          <h2>How It Works</h2>
          <p>
            Our platform combines NLP, machine learning, and market data to give you a complete picture of your
            internship readiness.
          </p>
        </div>
        <div className="feature-grid">
          {features.map((feature) => (
            <article key={feature.title} className="feature-card">
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
