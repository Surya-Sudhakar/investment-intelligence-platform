import { AssessmentDashboard } from "@/components/assessments/assessment-dashboard";
import { AssetIntelligenceDashboard } from "@/components/assets/asset-intelligence-dashboard";
import { DevelopmentStatus } from "@/components/status/development-status";
import { MarketDataScreen } from "@/components/market-data/market-data-screen";
import { IntelligenceDashboard } from "@/components/intelligence/intelligence-dashboard";
import { NewsIntelligenceDashboard } from "@/components/news/news-intelligence-dashboard";
import { MarketContextDashboard } from "@/components/market-context/market-context-dashboard";

export default function Home() {
  return (
    <>
      <DevelopmentStatus />
      <main className="mx-auto -mt-10 max-w-4xl px-6 pb-10 sm:px-10">
        <MarketDataScreen />
        <IntelligenceDashboard />
        <AssessmentDashboard />
        <AssetIntelligenceDashboard />
        <NewsIntelligenceDashboard />
        <MarketContextDashboard />
      </main>
    </>
  );
}
