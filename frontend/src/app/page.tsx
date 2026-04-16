"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { AppShell } from "@/components/app-shell";
import { BottomNav, TopNavTabs, type TabValue } from "@/components/bottom-nav";
import { CustomerHero } from "@/components/customer-hero";
import { InsightFeed } from "@/components/insight-feed";
import { GoalsView } from "@/components/goals-view";
import { ProductSearch } from "@/components/product-search";
import { RecentTransactions } from "@/components/recent-transactions";
import { DemoPanel } from "@/components/demo-panel";
import { useT } from "@/lib/i18n";

const CUSTOMER_ID = "C001";
const CUSTOMER_NAME = "Nguyễn Minh Anh";
const CUSTOMER_INITIALS = "MA";

export default function Home() {
  return (
    <Suspense fallback={null}>
      <HomeInner />
    </Suspense>
  );
}

function HomeInner() {
  const searchParams = useSearchParams();
  const initialTab = (searchParams.get("tab") as TabValue) || "feed";
  const demoMode = searchParams.get("demo") === "1";
  const [tab, setTab] = useState<TabValue>(initialTab);
  const [refreshKey, setRefreshKey] = useState(0);
  const [analysing, setAnalysing] = useState(false);
  const { t } = useT();

  const handleAgentPending = () => {
    setRefreshKey((k) => k + 1);
    setAnalysing(true);
    // Hard cap — if the agent takes too long or decides to stay silent
    // we still clear the skeleton so the feed doesn't pulse forever.
    setTimeout(() => setAnalysing(false), 45_000);
  };

  const handleCardArrived = () => {
    setAnalysing(false);
  };

  const handleDemoReset = () => {
    setAnalysing(false);
    setRefreshKey((k) => k + 1);
  };

  // Keep tab in sync when the URL changes (e.g. quick-prompt chip navigates to ?tab=plan).
  useEffect(() => {
    const urlTab = searchParams.get("tab") as TabValue | null;
    if (urlTab && (urlTab === "feed" || urlTab === "plan" || urlTab === "products")) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTab(urlTab);
    }
  }, [searchParams]);

  const goalPreset = {
    name: searchParams.get("goal_name") ?? undefined,
    amount: searchParams.get("goal_amount") ?? undefined,
    months: searchParams.get("goal_months") ?? undefined,
  };
  const productsQuery = searchParams.get("q") ?? undefined;

  return (
    <AppShell customerInitials={CUSTOMER_INITIALS}>
      <TopNavTabs value={tab} onChange={setTab} />
      <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
        <TabsContent value="feed" className="flex flex-col gap-4">
          <CustomerHero
            name={CUSTOMER_NAME}
            monthlyIncome={12097856}
            monthlySpending={24845043}
          />
          <RecentTransactions customerId={CUSTOMER_ID} refreshKey={refreshKey} />
          <InsightFeed
            customerId={CUSTOMER_ID}
            refreshKey={refreshKey}
            analysing={analysing}
            onCardArrived={handleCardArrived}
          />
        </TabsContent>

        <TabsContent value="plan" className="flex flex-col gap-4">
          <GoalsView customerId={CUSTOMER_ID} goalPreset={goalPreset} />
        </TabsContent>

        <TabsContent value="products" className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <h2 className="text-sm font-semibold tracking-tight">{t("products_heading")}</h2>
            <p className="text-xs text-muted-foreground">{t("products_subheading")}</p>
          </div>
          <ProductSearch initialQuery={productsQuery} />
        </TabsContent>
      </Tabs>

      <BottomNav value={tab} onChange={setTab} />

      {demoMode && (
        <DemoPanel
          customerId={CUSTOMER_ID}
          onInjected={handleAgentPending}
          onReset={handleDemoReset}
        />
      )}
    </AppShell>
  );
}
