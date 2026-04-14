import { ChartPie, Cpu, Rocket, Upload } from "lucide-react";

const steps = [
  {
    title: "Upload Resume",
    description: "Upload your resume in PDF or DOCX format",
    icon: Upload,
  },
  {
    title: "AI Analysis",
    description: "NLP extracts skills, education & experience",
    icon: Cpu,
  },
  {
    title: "Score & Gaps",
    description: "ML model computes readiness & identifies gaps",
    icon: ChartPie,
  },
  {
    title: "Get Recommendations",
    description: "Receive personalized improvement pathways",
    icon: Rocket,
  },
];

export function HowItWorksSection() {
  return (
    <section className="section section-tinted process-section">
      <div className="container">
        <div className="section-heading center process-heading">
          <h2>Simple 4-Step Process</h2>
          <p>From resume upload to actionable insights in seconds.</p>
        </div>
        <div className="steps-wrapper">
          <div className="connecting-line" />
          <div className="step-grid process-step-grid">
          {steps.map((step, index) => (
            <article key={step.title} className="step-card process-step-card">
              <div className="step-icon-box">
                <span className="step-badge">{index + 1}</span>
                <step.icon size={27} strokeWidth={2.2} />
              </div>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </article>
          ))}
          </div>
        </div>
      </div>
    </section>
  );
}
