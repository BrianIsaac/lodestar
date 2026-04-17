"use client";

import { useCallback, useEffect, useState } from "react";
import { Brain, RefreshCw } from "lucide-react";
import {
  fetchMemory,
  type MemoryCohortInsight,
  type MemoryLesson,
  type MemoryReflection,
  type MemorySnapshot,
} from "@/lib/api";
import { useT, type StringKey } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";

interface Props {
  customerId: string;
}

const QUADRANT_KEY: Record<string, StringKey> = {
  earned_reward: "memory_quadrant_earned_reward",
  bad_luck: "memory_quadrant_bad_luck",
  dumb_luck: "memory_quadrant_dumb_luck",
  just_desserts: "memory_quadrant_just_desserts",
};

export function MemoryPanel({ customerId }: Props) {
  const { t } = useT();
  const [snapshot, setSnapshot] = useState<MemorySnapshot | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("loading");

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const data = await fetchMemory(customerId);
      setSnapshot(data);
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  }, [customerId]);

  useEffect(() => {
    load();
  }, [load]);

  const lessons = snapshot?.lessons ?? [];
  const reflections = snapshot?.reflections ?? [];
  const cohort = snapshot?.cohort_insights ?? [];
  const cohortKey = snapshot?.cohort_key ?? "—";

  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <header className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Brain className="size-4 text-primary" />
          <h4 className="text-sm font-semibold">{t("memory_title")}</h4>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={load}
          disabled={status === "loading"}
          aria-label={t("memory_refresh")}
        >
          <RefreshCw className="size-3.5" />
        </Button>
      </header>
      <p className="text-[11px] leading-snug text-muted-foreground">
        {t("memory_description")}
      </p>

      {status === "loading" && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Spinner className="size-4 text-primary" />
          {t("memory_loading")}
        </div>
      )}

      {status === "error" && (
        <p className="text-xs text-destructive">{t("memory_error")}</p>
      )}

      {status === "idle" && snapshot ? (
        <>
          {lessons.length === 0 &&
          reflections.length === 0 &&
          cohort.length === 0 ? (
            <p className="rounded-md border border-dashed border-border bg-muted/30 p-3 text-[11px] text-muted-foreground">
              {t("memory_empty")}
            </p>
          ) : null}

          {lessons.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <h5 className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                {t("memory_section_lessons", { count: String(lessons.length) })}
              </h5>
              <ul className="flex flex-col gap-1.5">
                {lessons.map((L) => (
                  <LessonRow key={L.lesson_id} lesson={L} />
                ))}
              </ul>
            </div>
          )}

          {reflections.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <h5 className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                {t("memory_section_reflections", {
                  count: String(reflections.length),
                })}
              </h5>
              <ul className="flex flex-col gap-1.5">
                {reflections.map((R) => (
                  <ReflectionRow key={R.reflection_id} reflection={R} />
                ))}
              </ul>
            </div>
          )}

          {cohort.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <h5 className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                {t("memory_section_cohort", {
                  key: cohortKey,
                  count: String(cohort.length),
                })}
              </h5>
              <ul className="flex flex-col gap-1.5">
                {cohort.map((C) => (
                  <CohortRow key={`${C.pattern_type}-${C.category}`} insight={C} />
                ))}
              </ul>
            </div>
          )}
        </>
      ) : null}
    </section>
  );
}

function LessonRow({ lesson }: { lesson: MemoryLesson }) {
  const { t } = useT();
  const confidencePct = Math.round(lesson.confidence * 100);
  return (
    <li className="flex flex-col gap-1 rounded-md border border-border bg-background px-2.5 py-1.5">
      <p className="text-xs leading-snug">{lesson.insight}</p>
      <p className="text-[10px] text-muted-foreground">
        {lesson.conditions}
      </p>
      <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
        <Badge variant="secondary">
          {t("memory_confidence")} {confidencePct}%
        </Badge>
        <Badge variant="outline">
          {t("memory_importance")} {lesson.importance.toFixed(1)}
        </Badge>
        {lesson.times_evolved > 0 && (
          <Badge variant="outline">
            {t("memory_evolved")} ×{lesson.times_evolved}
          </Badge>
        )}
      </div>
    </li>
  );
}

function ReflectionRow({ reflection }: { reflection: MemoryReflection }) {
  const { t } = useT();
  const quadrantKey = QUADRANT_KEY[reflection.quadrant];
  return (
    <li className="flex items-center justify-between gap-2 rounded-md border border-border bg-background px-2.5 py-1.5 text-[11px]">
      <div className="flex flex-col">
        <span className="font-medium">
          {quadrantKey ? t(quadrantKey) : reflection.quadrant}
        </span>
        <span className="text-[10px] text-muted-foreground">
          {reflection.interaction_id} · {reflection.process_grade}/
          {reflection.outcome_quality}
        </span>
      </div>
      {reflection.lesson_extracted ? (
        <Badge variant="default" className="shrink-0">
          {t("memory_lesson_badge")}
        </Badge>
      ) : null}
    </li>
  );
}

function CohortRow({ insight }: { insight: MemoryCohortInsight }) {
  return (
    <li className="flex flex-col gap-0.5 rounded-md border border-border bg-background px-2.5 py-1.5 text-[11px]">
      <p className="leading-snug">{insight.insight}</p>
      <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-muted-foreground">
        <span>{insight.pattern_type}</span>
        <span>· n={insight.supporting_count}</span>
      </div>
    </li>
  );
}
