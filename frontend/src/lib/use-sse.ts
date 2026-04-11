"use client";

import { useEffect, useState } from "react";
import type { InsightCard } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Hook to consume SSE insight stream from the backend. */
export function useInsightStream(customerId: string) {
  const [insights, setInsights] = useState<InsightCard[]>([]);

  useEffect(() => {
    const es = new EventSource(`${API}/stream/${customerId}`);

    es.addEventListener("insight", (event) => {
      try {
        const data = JSON.parse(event.data) as InsightCard;
        setInsights((prev) => {
          if (prev.some((i) => i.insight_id === data.insight_id)) return prev;
          return [data, ...prev];
        });
      } catch {
        // skip malformed events
      }
    });

    es.onerror = () => {
      es.close();
    };

    return () => es.close();
  }, [customerId]);

  return insights;
}
