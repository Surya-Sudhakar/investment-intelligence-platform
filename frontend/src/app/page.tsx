import { AssessmentDashboard } from "@/components/assessments/assessment-dashboard";
import { DevelopmentStatus } from "@/components/status/development-status";
import { MarketDataScreen } from "@/components/market-data/market-data-screen";
import { IntelligenceDashboard } from "@/components/intelligence/intelligence-dashboard";

export default function Home() {
  return (
    <>
      <DevelopmentStatus />
      <main className="mx-auto -mt-10 max-w-4xl px-6 pb-10 sm:px-10">
        <MarketDataScreen />
        <IntelligenceDashboard />
        <AssessmentDashboard />
      </main>
    </>
  );
}
