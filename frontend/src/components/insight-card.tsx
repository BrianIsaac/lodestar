"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChartRenderer } from "@/components/chart-renderer";
import type { InsightCard as InsightCardType } from "@/lib/types";

const SEVERITY_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  life_event: "destructive",
  anomaly: "default",
  milestone: "secondary",
  info: "outline",
  product: "secondary",
};

export function InsightCard({ card }: { card: InsightCardType }) {
  return (
    <Link href={`/insight/${card.insight_id}`}>
      <Card className="cursor-pointer transition-colors hover:border-primary">
        <CardHeader className="flex flex-row items-center justify-between gap-2 pb-2">
          <CardTitle className="text-sm font-medium leading-tight">
            {card.title}
          </CardTitle>
          <Badge variant={SEVERITY_VARIANT[card.severity] ?? "outline"}>
            {card.severity.replace("_", " ")}
          </Badge>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-sm text-muted-foreground">{card.summary}</p>
          {card.chart_spec && <ChartRenderer spec={card.chart_spec} />}
        </CardContent>
      </Card>
    </Link>
  );
}
