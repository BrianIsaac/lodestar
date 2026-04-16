"use client";

import { useState } from "react";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { AppShell } from "@/components/app-shell";
import { BottomNav, TopNavTabs, type TabValue } from "@/components/bottom-nav";
import { CustomerHero } from "@/components/customer-hero";
import { InsightFeed } from "@/components/insight-feed";
import { GoalsView } from "@/components/goals-view";
import { ProductSearch } from "@/components/product-search";
import { useT } from "@/lib/i18n";

const CUSTOMER_ID = "C001";
const CUSTOMER_NAME = "Nguyễn Minh Anh";
const CUSTOMER_INITIALS = "MA";

export default function Home() {
  const [tab, setTab] = useState<TabValue>("feed");
  const { t } = useT();

  return (
    <AppShell customerInitials={CUSTOMER_INITIALS}>
      <TopNavTabs value={tab} onChange={setTab} />
      <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
        <TabsContent value="feed" className="flex flex-col gap-4">
          <CustomerHero name={CUSTOMER_NAME} monthlyIncome={12097856} monthlySpending={24845043} />
          <InsightFeed customerId={CUSTOMER_ID} />
        </TabsContent>

        <TabsContent value="plan" className="flex flex-col gap-4">
          <GoalsView customerId={CUSTOMER_ID} />
        </TabsContent>

        <TabsContent value="products" className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <h2 className="text-sm font-semibold tracking-tight">{t("products_heading")}</h2>
            <p className="text-xs text-muted-foreground">{t("products_subheading")}</p>
          </div>
          <ProductSearch />
        </TabsContent>
      </Tabs>

      <BottomNav value={tab} onChange={setTab} />
    </AppShell>
  );
}
