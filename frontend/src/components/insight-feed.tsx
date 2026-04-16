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

  useEffect(() => {
    let cancelled = false;
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
        toast.error("Không thể bỏ qua insight. Vui lòng thử lại.");
      });
      toast.success("Đã bỏ qua. Coach sẽ ghi nhận phản hồi.");
    },
    [customerId]
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
          <EmptyTitle>Chưa có insight nào</EmptyTitle>
          <EmptyDescription>
            Coach đang theo dõi giao dịch của bạn. Quay lại sau ít phút.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <Alert>
        <Sparkles />
        <AlertDescription>
          Lodestar cung cấp thông tin tham khảo, không phải tư vấn tài chính.
        </AlertDescription>
      </Alert>
      {cards.map((card) => (
        <InsightCard key={card.insight_id} card={card} onDismiss={handleDismiss} />
      ))}
    </div>
  );
}
