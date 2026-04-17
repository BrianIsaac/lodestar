"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Radio, Sparkles, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
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
import { useLayoutMode } from "@/lib/layout-mode";
import { useInsightStream } from "@/lib/use-sse";
import type { InsightCard as InsightCardType } from "@/lib/types";

interface Props {
  customerId: string;
  /** Bumped by the parent when a demo transaction is injected, forcing a
   *  REST refetch in addition to the SSE diff stream. */
  refreshKey?: number;
  /** True while a detector agent is reasoning about a newly-injected
   *  transaction. Renders a pulsing "Coach is analysing…" skeleton at
   *  the top of the feed until a real card arrives via SSE or the
   *  parent clears it. */
  analysing?: boolean;
  /** Called when a new SSE card lands so the parent can clear
   *  `analysing` and stop the skeleton. */
  onCardArrived?: (insightId: string) => void;
}

type FeedState =
  | { status: "loading" }
  | { status: "ready"; cards: InsightCardType[] };

export function InsightFeed({
  customerId,
  refreshKey = 0,
  analysing = false,
  onCardArrived,
}: Props) {
  const [state, setState] = useState<FeedState>({ status: "loading" });
  const { t } = useT();
  const { mode } = useLayoutMode();
  const stream = useInsightStream(customerId);
  const lastSeenStreamIdRef = useRef<string | null>(null);
  const cardGridClass =
    mode === "web"
      ? "grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3"
      : "flex flex-col gap-3";

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
    // client-side renders. We refetch when customerId or refreshKey
    // (demo transaction injection) changes.
    fetchFeed(customerId)
      .then((feed) => {
        if (!cancelled) setState({ status: "ready", cards: feed.cards });
      })
      .catch(() => {
        if (cancelled) return;
        toast.error(t("feed_fetch_error"));
        setState({ status: "ready", cards: [] });
      });
    return () => {
      cancelled = true;
    };
    // t is stable per render; only refetch on data-source changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId, refreshKey]);

  // Notify the parent whenever a new SSE card arrives so it can clear
  // the "Coach is analysing…" skeleton.
  useEffect(() => {
    if (!stream.cards.length) return;
    const latest = stream.cards[0];
    if (!latest?.insight_id) return;
    if (lastSeenStreamIdRef.current === latest.insight_id) return;
    lastSeenStreamIdRef.current = latest.insight_id;
    onCardArrived?.(latest.insight_id);
  }, [stream.cards, onCardArrived]);

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
      <div className={cardGridClass}>
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (cards.length === 0 && !analysing) {
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
      <Alert className="py-2">
        <Sparkles className="size-3.5" />
        <AlertDescription className="text-[11px] leading-snug">
          {t("compliance_banner")}
        </AlertDescription>
      </Alert>
      <div className={cardGridClass}>
        {analysing && <AnalysingSkeleton />}
        {cards.map((card) => {
          // Cards delivered by the SSE stream get a brief entrance pulse
          // so the audience sees the agent react live.
          const arrivedLive = stream.cards.some(
            (c) => c.insight_id === card.insight_id
          );
          return (
            <InsightCard
              key={card.insight_id}
              card={card}
              onDismiss={handleDismiss}
              justArrived={arrivedLive}
            />
          );
        })}
      </div>
    </div>
  );
}

function AnalysingSkeleton() {
  const { t } = useT();
  return (
    <Card className="relative overflow-hidden border-l-4 border-l-primary/60 bg-primary/5">
      <CardContent className="flex flex-col gap-3 p-4">
        <div className="flex items-start gap-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/15">
            <Loader2 className="size-5 animate-spin text-primary" />
          </span>
          <div className="flex min-w-0 flex-col gap-1">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-primary">
              {t("coach_analysing_title")}
            </span>
            <p className="text-xs leading-snug text-muted-foreground">
              {t("coach_analysing_desc")}
            </p>
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <Skeleton className="h-2 w-3/4 rounded" />
          <Skeleton className="h-2 w-11/12 rounded" />
          <Skeleton className="h-2 w-2/3 rounded" />
        </div>
      </CardContent>
    </Card>
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
