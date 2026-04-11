"use client";

import { useEffect, useState } from "react";
import { InsightCard } from "@/components/insight-card";
import { fetchFeed } from "@/lib/api";
import type { InsightCard as InsightCardType } from "@/lib/types";

export function InsightFeed({ customerId }: { customerId: string }) {
  const [cards, setCards] = useState<InsightCardType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFeed(customerId)
      .then((feed) => setCards(feed.cards))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [customerId]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-40 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    );
  }

  if (cards.length === 0) {
    return (
      <p className="text-center text-muted-foreground">
        No insights yet. Check back soon.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {cards.map((card) => (
        <InsightCard key={card.insight_id} card={card} />
      ))}
    </div>
  );
}
