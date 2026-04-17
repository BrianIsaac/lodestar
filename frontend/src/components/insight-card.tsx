"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronRight, Lightbulb, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChartRenderer } from "@/components/chart-renderer";
import { cn } from "@/lib/utils";
import { getSeverityMeta } from "@/components/severity";
import { useT } from "@/lib/i18n";
import type { InsightCard as InsightCardType, QuickPrompt } from "@/lib/types";

interface Props {
  card: InsightCardType;
  onDismiss?: (id: string) => void;
  /** When true the card renders with a subtle entrance pulse — used when a
   *  card arrives via SSE so the audience sees it land. */
  justArrived?: boolean;
}

export function InsightCard({ card, onDismiss, justArrived }: Props) {
  const meta = getSeverityMeta(card.severity);
  const Icon = meta.icon;
  const { lang, t } = useT();
  const router = useRouter();
  const title = card.title_i18n?.[lang] ?? card.title;
  const summary = card.summary_i18n?.[lang] ?? card.summary;
  const actionHints = card.action_hint_i18n?.[lang] ?? [];
  const quickPrompts = card.quick_prompts_i18n?.[lang] ?? [];

  function dispatchPrompt(prompt: QuickPrompt) {
    if (prompt.action === "plan") {
      const params = new URLSearchParams({ tab: "plan" });
      const p = prompt.params ?? {};
      if (typeof p.name === "string") params.set("goal_name", p.name);
      if (typeof p.target_amount === "number") params.set("goal_amount", String(p.target_amount));
      if (typeof p.months === "number") params.set("goal_months", String(p.months));
      router.push(`/?${params.toString()}`);
      return;
    }
    if (prompt.action === "products") {
      const params = new URLSearchParams({ tab: "products" });
      const q = prompt.params?.query;
      if (typeof q === "string") params.set("q", q);
      router.push(`/?${params.toString()}`);
      return;
    }
    // Default: chat → open drill-down with the prompt pre-submitted.
    const params = new URLSearchParams({ q: prompt.text });
    router.push(`/insight/${card.insight_id}?${params.toString()}`);
  }

  return (
    <Card
      className={cn(
        "relative overflow-hidden border-l-4 p-0 transition-shadow hover:shadow-md",
        meta.borderClass,
        justArrived && "ring-2 ring-primary/60 animate-in fade-in slide-in-from-top-2 duration-500"
      )}
    >
      {onDismiss && (
        <Button
          type="button"
          variant="ghost"
          size="icon-xs"
          aria-label={t("dismiss_aria")}
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
      <div className="flex flex-col gap-3 p-4">
        <Link
          href={`/insight/${card.insight_id}`}
          className="flex items-start gap-3 rounded-lg pr-8 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:ring-offset-2"
        >
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
              <Badge variant={meta.badgeVariant}>{t(meta.labelKey)}</Badge>
            </div>
            <h3 className="text-sm font-semibold leading-tight">{title}</h3>
            <p className="text-xs text-muted-foreground">{summary}</p>
          </div>
        </Link>

        {card.chart_spec && (
          <div className="rounded-lg border border-border/70 bg-muted/40 p-2">
            <ChartRenderer spec={card.chart_spec} compact />
          </div>
        )}

        {actionHints.length > 0 && (
          <div className="flex flex-col gap-2 rounded-lg border border-border/60 bg-muted/30 p-3">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-primary">
              <Lightbulb className="size-3.5" />
              {t("card_action_header")}
            </div>
            <ul className="flex list-disc flex-col gap-1 pl-5 text-xs text-foreground">
              {actionHints.map((hint, i) => (
                <li key={i} className="leading-snug">
                  {hint}
                </li>
              ))}
            </ul>
          </div>
        )}

        {quickPrompts.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {quickPrompts.map((prompt, i) => (
              <button
                key={i}
                type="button"
                onClick={() => dispatchPrompt(prompt)}
                className={cn(
                  "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                  prompt.action === "plan" || prompt.action === "products"
                    ? "border-primary/50 bg-primary/10 text-primary hover:bg-primary/20"
                    : "border-border bg-background text-foreground hover:bg-muted"
                )}
              >
                {prompt.text}
              </button>
            ))}
          </div>
        )}

        <Link
          href={`/insight/${card.insight_id}`}
          className="flex items-center justify-end rounded-md text-xs text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:ring-offset-2"
        >
          <span className="flex items-center gap-1">
            {t("card_cta")}
            <ChevronRight className="size-3.5" />
          </span>
        </Link>
      </div>
    </Card>
  );
}
