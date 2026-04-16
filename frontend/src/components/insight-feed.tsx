"use client";

import { useCallback, useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
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
import { dismissInsight, fetchFeed } from "@/lib/api";
import { useT } from "@/lib/i18n";
import type { InsightCard as InsightCardType } from "@/lib/types";

interface Props {
  customerId: string;
}

type FeedState =
  | { status: "loading" }
  | { status: "ready"; cards: InsightCardType[] };

export function InsightFeed({ customerId }: Props) {
  const [state, setState] = useState<FeedState>({ status: "loading" });
  const cards = state.status === "ready" ? state.cards : [];
  const loading = state.status === "loading";
  const { lang, t } = useT();

  useEffect(() => {
    let cancelled = false;
    // Reset to loading when customerId or language changes so the user sees
    // skeletons while the backend re-translates the feed.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setState({ status: "loading" });
    fetchFeed(customerId, lang)
      .then((feed) => {
        if (!cancelled) setState({ status: "ready", cards: feed.cards });
      })
      .catch(() => {
        if (!cancelled) setState({ status: "ready", cards: [] });
      });
    return () => {
      cancelled = true;
    };
  }, [customerId, lang]);

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
