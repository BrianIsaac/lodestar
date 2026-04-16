"use client";

import { useState } from "react";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { AppShell } from "@/components/app-shell";
import { BottomNav, type TabValue } from "@/components/bottom-nav";
import { CustomerHero } from "@/components/customer-hero";
import { InsightFeed } from "@/components/insight-feed";
import { GoalsView } from "@/components/goals-view";
import { ProductSearch } from "@/components/product-search";

const CUSTOMER_ID = "C001";
const CUSTOMER_NAME = "Nguyễn Minh Anh";
const CUSTOMER_INITIALS = "MA";

export default function Home() {
  const [tab, setTab] = useState<TabValue>("feed");

  return (
    <AppShell customerInitials={CUSTOMER_INITIALS}>
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
            <h2 className="text-sm font-semibold tracking-tight">Sản phẩm Shinhan</h2>
            <p className="text-xs text-muted-foreground">
              Tìm kiếm thẻ tín dụng, vay, bảo hiểm và đầu tư bằng tiếng Việt.
            </p>
          </div>
          <ProductSearch />
        </TabsContent>
      </Tabs>

      <BottomNav value={tab} onChange={setTab} />
    </AppShell>
  );
}
