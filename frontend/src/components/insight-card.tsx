"use client";

import Link from "next/link";
import { ChevronRight, X } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChartRenderer } from "@/components/chart-renderer";
import { cn } from "@/lib/utils";
import { getSeverityMeta } from "@/components/severity";
import type { InsightCard as InsightCardType } from "@/lib/types";

interface Props {
  card: InsightCardType;
  onDismiss?: (id: string) => void;
}

export function InsightCard({ card, onDismiss }: Props) {
  const meta = getSeverityMeta(card.severity);
  const Icon = meta.icon;

  return (
    <Card
      className={cn(
        "relative overflow-hidden border-l-4 p-0 transition-shadow hover:shadow-md",
        meta.borderClass
      )}
    >
      {onDismiss && (
        <Button
          type="button"
          variant="ghost"
          size="icon-xs"
          aria-label="Bỏ qua"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onDismiss(card.insight_id);
          }}
          className="absolute top-2 right-2 z-10"
        >
          <X />
        </Button>
      )}
      <Link
        href={`/insight/${card.insight_id}`}
        className="block focus-visible:outline-none"
      >
        <CardContent className="flex flex-col gap-3 p-4">
          <div className="flex items-start gap-3 pr-8">
            <span
              className={cn(
                "flex size-10 shrink-0 items-center justify-center rounded-xl",
                meta.iconBgClass
              )}
            >
              <Icon className={cn("size-5", meta.iconColorClass)} />
            </span>
            <div className="flex min-w-0 flex-col gap-1">
              <div className="flex items-center gap-2">
                <Badge variant={meta.badgeVariant}>{meta.labelVi}</Badge>
              </div>
              <h3 className="text-sm font-semibold leading-tight">{card.title}</h3>
              <p className="text-xs text-muted-foreground">{card.summary}</p>
            </div>
          </div>

          {card.chart_spec && (
            <div className="rounded-lg border border-border/70 bg-muted/40 p-2">
              <ChartRenderer spec={card.chart_spec} compact />
            </div>
          )}

          <div className="flex items-center justify-end text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              Xem chi tiết
              <ChevronRight className="size-3.5" />
            </span>
          </div>
        </CardContent>
      </Link>
    </Card>
  );
}
