"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ChartRenderer } from "@/components/chart-renderer";
import { DrillDownChat } from "@/components/drill-down-chat";
import { AppShell } from "@/components/app-shell";
import { getSeverityMeta } from "@/components/severity";
import { cn } from "@/lib/utils";
import { fetchFeed } from "@/lib/api";
import type { InsightCard as InsightCardType } from "@/lib/types";

const CUSTOMER_ID = "C001";
const CUSTOMER_INITIALS = "MA";

export default function InsightPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [card, setCard] = useState<InsightCardType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchFeed(CUSTOMER_ID)
      .then((feed) => {
        if (cancelled) return;
        setCard(feed.cards.find((c) => c.insight_id === id) ?? null);
      })
      .catch(() => {
        if (!cancelled) setCard(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  return (
    <AppShell customerInitials={CUSTOMER_INITIALS}>
      <div className="flex flex-col gap-4">
        <Link href="/" className="inline-flex">
          <Button variant="ghost" size="sm" className="-ml-2">
            <ArrowLeft data-icon="inline-start" />
            Quay lại bảng tin
          </Button>
        </Link>

        {loading ? (
          <Skeleton className="h-40 w-full rounded-xl" />
        ) : card ? (
          <InsightContext card={card} />
        ) : (
          <Card className="border-dashed">
            <CardContent className="p-4 text-sm text-muted-foreground">
              Không tìm thấy insight. Có thể đã bị bỏ qua.
            </CardContent>
          </Card>
        )}

        <DrillDownChat
          insightId={id}
          customerId={CUSTOMER_ID}
          initialContext={
            card ? `${card.title}\n${card.summary}` : `Insight ID: ${id}`
          }
        />
      </div>
    </AppShell>
  );
}

function InsightContext({ card }: { card: InsightCardType }) {
  const meta = getSeverityMeta(card.severity);
  const Icon = meta.icon;
  return (
    <Card className={cn("overflow-hidden border-l-4 p-0", meta.borderClass)}>
      <CardContent className="flex flex-col gap-3 p-4">
        <div className="flex items-start gap-3">
          <span
            className={cn(
              "flex size-10 shrink-0 items-center justify-center rounded-xl",
              meta.iconBgClass
            )}
          >
            <Icon className={cn("size-5", meta.iconColorClass)} />
          </span>
          <div className="flex flex-col gap-1">
            <Badge variant={meta.badgeVariant} className="self-start">
              {meta.labelVi}
            </Badge>
            <h1 className="text-base font-semibold leading-tight">{card.title}</h1>
            <p className="text-sm text-muted-foreground">{card.summary}</p>
          </div>
        </div>

        {card.chart_spec && (
          <div className="rounded-lg border border-border/70 bg-muted/40 p-2">
            <ChartRenderer spec={card.chart_spec} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
