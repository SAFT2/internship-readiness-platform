import { FeaturesSection } from "../components/FeaturesSection";
import { Footer } from "../components/Footer";
import { HeroSection } from "../components/HeroSection";
import { HowItWorksSection } from "../components/HowItWorksSection";

export function HomePage() {
  return (
    <>
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <Footer />
    </>
  );
}
