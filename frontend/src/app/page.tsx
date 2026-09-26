import { LandingBackground } from "@/components/landing/landing-background";
import { SiteNav } from "@/components/landing/site-nav";
import { Hero } from "@/components/landing/hero";
import { HowItWorks } from "@/components/landing/how-it-works";
import { Features } from "@/components/landing/features";
import { Faq } from "@/components/landing/faq";
import { CtaFooter } from "@/components/landing/cta-footer";

export default function LandingPage() {
  return (
    <>
      <LandingBackground />
      <div className="relative z-10 flex flex-1 flex-col">
        <SiteNav />
        <main className="flex-1">
          <Hero />
          <HowItWorks />
          <Features />
          <Faq />
          <CtaFooter />
        </main>
      </div>
    </>
  );
}
