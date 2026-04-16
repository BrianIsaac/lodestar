"use client";

import { useEffect, useState } from "react";
import type { InsightCard } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type StreamStatus = "connecting" | "live" | "closed";

interface StreamState {
  status: StreamStatus;
  cards: InsightCard[];
}

/** Hook to consume the backend's SSE insight stream.
 *
 *  Opens an EventSource to `/stream/{customerId}`, accumulates unique cards
 *  by `insight_id`, and exposes a connection status so the UI can show a
 *  LIVE indicator. The stream sends a partial InsightCard payload (no
 *  chart_spec or compliance_class) — that's enough for feed-level rendering;
 *  the REST `/feed` call fills in the full record. */
export function useInsightStream(customerId: string): StreamState {
  const [state, setState] = useState<StreamState>({ status: "connecting", cards: [] });

  useEffect(() => {
    const es = new EventSource(`${API}/stream/${customerId}`);

    es.onopen = () => {
      setState((prev) => ({ ...prev, status: "live" }));
    };

    es.addEventListener("insight", (event) => {
      try {
        const partial = JSON.parse((event as MessageEvent).data) as Partial<InsightCard>;
        if (!partial.insight_id) return;
        setState((prev) => {
          if (prev.cards.some((c) => c.insight_id === partial.insight_id)) return prev;
          const normalised: InsightCard = {
            insight_id: partial.insight_id ?? "",
            customer_id: partial.customer_id ?? customerId,
            title: partial.title ?? "",
            summary: partial.summary ?? "",
            severity: partial.severity ?? "info",
            chart_spec: partial.chart_spec ?? null,
            suggested_actions: partial.suggested_actions ?? [],
            compliance_class: partial.compliance_class ?? "information",
            priority_score: partial.priority_score ?? 0,
            dismissed: partial.dismissed ?? false,
          };
          return { status: "live", cards: [normalised, ...prev.cards] };
        });
      } catch {
        // skip malformed payloads
      }
    });

    es.onerror = () => {
      setState((prev) => ({ ...prev, status: "closed" }));
      es.close();
    };

    return () => {
      es.close();
    };
  }, [customerId]);

  return state;
}
