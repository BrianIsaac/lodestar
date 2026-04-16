"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Radio, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { InsightCard } from "@/components/insight-card";
import { cn } from "@/lib/utils";
import { dismissInsight, fetchFeed } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { useInsightStream } from "@/lib/use-sse";
import type { InsightCard as InsightCardType } from "@/lib/types";

interface Props {
  customerId: string;
}

type FeedState =
  | { status: "loading" }
  | { status: "ready"; cards: InsightCardType[] };

export function InsightFeed({ customerId }: Props) {
  const [state, setState] = useState<FeedState>({ status: "loading" });
  const { t } = useT();
  const stream = useInsightStream(customerId);

  const loading = state.status === "loading";

  // Merge REST cards (authoritative for language + chart_spec) with live
  // SSE arrivals not already in the REST set. Live cards are prepended so
  // new arrivals appear at the top of the feed.
  const cards = useMemo<InsightCardType[]>(() => {
    if (state.status !== "ready") return [];
    const restIds = new Set(state.cards.map((c) => c.insight_id));
    const liveExtras = stream.cards.filter((c) => !restIds.has(c.insight_id));
    return [...liveExtras, ...state.cards];
  }, [state, stream.cards]);

  useEffect(() => {
    let cancelled = false;
    // Cards carry title_i18n/summary_i18n, so language toggles are pure
    // client-side renders — no refetch needed when lang changes.
    fetchFeed(customerId)
      .then((feed) => {
        if (!cancelled) setState({ status: "ready", cards: feed.cards });
      })
      .catch(() => {
        if (!cancelled) setState({ status: "ready", cards: [] });
      });
    return () => {
      cancelled = true;
    };
  }, [customerId]);

  const handleDismiss = useCallback(
    (insightId: string) => {
      let previous: InsightCardType[] = [];
      setState((s) => {
        if (s.status !== "ready") return s;
        previous = s.cards;
        return { status: "ready", cards: s.cards.filter((c) => c.insight_id !== insightId) };
      });
      dismissInsight(insightId, customerId).catch(() => {
        setState({ status: "ready", cards: previous });
        toast.error(t("dismiss_error"));
      });
      toast.success(t("dismiss_success"));
    },
    [customerId, t]
  );

  if (loading) {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (cards.length === 0) {
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Sparkles />
          </EmptyMedia>
          <EmptyTitle>{t("feed_empty_title")}</EmptyTitle>
          <EmptyDescription>{t("feed_empty_desc")}</EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-end">
        <StreamStatusBadge status={stream.status} />
      </div>
      <Alert>
        <Sparkles />
        <AlertDescription>{t("compliance_banner")}</AlertDescription>
      </Alert>
      {cards.map((card) => (
        <InsightCard key={card.insight_id} card={card} onDismiss={handleDismiss} />
      ))}
    </div>
  );
}

function StreamStatusBadge({ status }: { status: "connecting" | "live" | "closed" }) {
  const { t } = useT();
  const active = status === "live";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
        active
          ? "bg-primary/10 text-primary"
          : "bg-muted text-muted-foreground"
      )}
      aria-label={t("stream_status_aria")}
    >
      <span
        className={cn(
          "inline-block size-1.5 rounded-full",
          active ? "bg-primary animate-pulse" : "bg-muted-foreground"
        )}
      />
      {active ? t("stream_live") : t("stream_offline")}
      <Radio className="size-2.5" />
    </span>
  );
}
