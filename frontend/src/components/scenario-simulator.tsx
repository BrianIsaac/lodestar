"use client";

import { useState } from "react";
import { Building2, PlayCircle, PiggyBank, Shield, TrendingUp } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { cn } from "@/lib/utils";
import { formatVND } from "@/lib/format";
import { simulateScenario } from "@/lib/api";
import { useT, type StringKey } from "@/lib/i18n";
import type { ScenarioResult } from "@/lib/types";

interface Props {
  customerId: string;
}

const ENTITY_META: Record<
  string,
  { icon: LucideIcon; labelKey: StringKey; colorClass: string }
> = {
  bank: { icon: Building2, labelKey: "entity_bank", colorClass: "text-chart-1" },
  finance: { icon: PiggyBank, labelKey: "entity_finance", colorClass: "text-chart-2" },
  securities: { icon: TrendingUp, labelKey: "entity_securities", colorClass: "text-chart-4" },
  life: { icon: Shield, labelKey: "entity_life", colorClass: "text-chart-5" },
};

type ScenarioType = "home_purchase" | "career_change" | "new_baby" | "marriage";

const SCENARIO_OPTIONS: {
  id: ScenarioType;
  labelKey: StringKey;
  titleKey: StringKey;
}[] = [
  {
    id: "home_purchase",
    labelKey: "sim_scenario_home",
    titleKey: "sim_card_title_home",
  },
  {
    id: "career_change",
    labelKey: "sim_scenario_career",
    titleKey: "sim_card_title_career",
  },
  {
    id: "new_baby",
    labelKey: "sim_scenario_baby",
    titleKey: "sim_card_title_baby",
  },
  {
    id: "marriage",
    labelKey: "sim_scenario_marriage",
    titleKey: "sim_card_title_marriage",
  },
];

export function ScenarioSimulator({ customerId }: Props) {
  const [scenario, setScenario] = useState<ScenarioType>("home_purchase");
  const [price, setPrice] = useState("2000000000");
  const [down, setDown] = useState("0.2");
  const [term, setTerm] = useState("240");
  const [rate, setRate] = useState("7.5");
  const [newIncome, setNewIncome] = useState("16000000");
  const [babyCost, setBabyCost] = useState("8000000");
  const [partnerIncome, setPartnerIncome] = useState("12000000");
  const [weddingCost, setWeddingCost] = useState("200000000");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { lang, t } = useT();

  function changeScenario(next: ScenarioType) {
    setScenario(next);
    // Stale results from the previous scenario would otherwise stay visible
    // below the form after a switch, misleading the user.
    setResult(null);
    setError(null);
  }

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const parameters =
        scenario === "home_purchase"
          ? {
              property_value: Number(price),
              down_payment_pct: Number(down),
              term_months: Number(term),
              interest_rate: Number(rate),
            }
          : scenario === "career_change"
            ? { new_income: Number(newIncome) }
            : scenario === "new_baby"
              ? { monthly_cost: Number(babyCost) }
              : {
                  partner_income: Number(partnerIncome),
                  wedding_cost: Number(weddingCost),
                };

      const res = await simulateScenario(customerId, scenario, parameters, lang);
      setResult(res);
    } catch {
      setError(t("sim_error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">
            {t(
              SCENARIO_OPTIONS.find((opt) => opt.id === scenario)?.titleKey ??
                "sim_card_title",
            )}
          </CardTitle>
          <CardDescription className="text-xs">{t("sim_card_desc")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={run}>
            <FieldGroup>
              <Field role="radiogroup" aria-label={t("sim_scenario_label")}>
                <FieldLabel>{t("sim_scenario_label")}</FieldLabel>
                <div
                  className="flex flex-wrap gap-1.5"
                  onKeyDown={(e) => {
                    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
                    e.preventDefault();
                    const idx = SCENARIO_OPTIONS.findIndex((o) => o.id === scenario);
                    const delta = e.key === "ArrowRight" ? 1 : -1;
                    const next = SCENARIO_OPTIONS[
                      (idx + delta + SCENARIO_OPTIONS.length) %
                        SCENARIO_OPTIONS.length
                    ];
                    changeScenario(next.id);
                    // Move focus to match the new selection — roving tabindex.
                    const btn = document.querySelector<HTMLButtonElement>(
                      `[data-scenario-radio="${next.id}"]`,
                    );
                    btn?.focus();
                  }}
                >
                  {SCENARIO_OPTIONS.map((opt) => {
                    const active = scenario === opt.id;
                    return (
                      <button
                        key={opt.id}
                        type="button"
                        role="radio"
                        aria-checked={active}
                        tabIndex={active ? 0 : -1}
                        data-scenario-radio={opt.id}
                        onClick={() => changeScenario(opt.id)}
                        className={cn(
                          "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                          active
                            ? "border-primary bg-primary text-primary-foreground"
                            : "border-border bg-background hover:bg-muted"
                        )}
                      >
                        {t(opt.labelKey)}
                      </button>
                    );
                  })}
                </div>
              </Field>
              {scenario === "home_purchase" ? (
                <>
                  <Field>
                    <FieldLabel htmlFor="sim-price">{t("sim_price")}</FieldLabel>
                    <Input
                      id="sim-price"
                      type="number"
                      value={price}
                      onChange={(e) => setPrice(e.target.value)}
                      min={0}
                    />
                    <FieldDescription>{t("sim_price_hint")}</FieldDescription>
                  </Field>
                  <div className="grid grid-cols-3 gap-3">
                    <Field>
                      <FieldLabel htmlFor="sim-down">{t("sim_down")}</FieldLabel>
                      <Input
                        id="sim-down"
                        type="number"
                        step="0.05"
                        value={down}
                        onChange={(e) => setDown(e.target.value)}
                        min={0}
                        max={1}
                      />
                    </Field>
                    <Field>
                      <FieldLabel htmlFor="sim-term">{t("sim_term")}</FieldLabel>
                      <Input
                        id="sim-term"
                        type="number"
                        value={term}
                        onChange={(e) => setTerm(e.target.value)}
                        min={12}
                      />
                    </Field>
                    <Field>
                      <FieldLabel htmlFor="sim-rate">{t("sim_rate")}</FieldLabel>
                      <Input
                        id="sim-rate"
                        type="number"
                        step="0.1"
                        value={rate}
                        onChange={(e) => setRate(e.target.value)}
                        min={0}
                      />
                    </Field>
                  </div>
                </>
              ) : null}
              {scenario === "career_change" ? (
                <Field>
                  <FieldLabel htmlFor="sim-new-income">
                    {t("sim_field_new_income")}
                  </FieldLabel>
                  <Input
                    id="sim-new-income"
                    type="number"
                    value={newIncome}
                    onChange={(e) => setNewIncome(e.target.value)}
                    min={0}
                  />
                  <FieldDescription>{t("sim_field_new_income_hint")}</FieldDescription>
                </Field>
              ) : null}
              {scenario === "new_baby" ? (
                <Field>
                  <FieldLabel htmlFor="sim-baby-cost">
                    {t("sim_field_baby_cost")}
                  </FieldLabel>
                  <Input
                    id="sim-baby-cost"
                    type="number"
                    value={babyCost}
                    onChange={(e) => setBabyCost(e.target.value)}
                    min={0}
                  />
                  <FieldDescription>{t("sim_field_baby_cost_hint")}</FieldDescription>
                </Field>
              ) : null}
              {scenario === "marriage" ? (
                <div className="grid grid-cols-2 gap-3">
                  <Field>
                    <FieldLabel htmlFor="sim-partner-income">
                      {t("sim_field_partner_income")}
                    </FieldLabel>
                    <Input
                      id="sim-partner-income"
                      type="number"
                      value={partnerIncome}
                      onChange={(e) => setPartnerIncome(e.target.value)}
                      min={0}
                    />
                    <FieldDescription>
                      {t("sim_field_partner_income_hint")}
                    </FieldDescription>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="sim-wedding-cost">
                      {t("sim_field_wedding_cost")}
                    </FieldLabel>
                    <Input
                      id="sim-wedding-cost"
                      type="number"
                      value={weddingCost}
                      onChange={(e) => setWeddingCost(e.target.value)}
                      min={0}
                    />
                    <FieldDescription>
                      {t("sim_field_wedding_cost_hint")}
                    </FieldDescription>
                  </Field>
                </div>
              ) : null}
            </FieldGroup>
            <Button type="submit" disabled={loading} className="mt-4 w-full">
              {loading ? (
                <>
                  <Spinner data-icon="inline-start" aria-label={t("sim_running")} />
                  {t("sim_running")}
                </>
              ) : (
                <>
                  <PlayCircle data-icon="inline-start" />
                  {t("sim_run")}
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>{t("sim_error_title")}</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {result ? <ScenarioResultView result={result} /> : null}
    </div>
  );
}

function ScenarioResultView({ result }: { result: ScenarioResult }) {
  const { t } = useT();
  const net = result.monthly_cashflow_after;
  const netNegative = net < 0;
  return (
    <div className="flex flex-col gap-3">
      <Card
        className={cn(
          "overflow-hidden border-l-4",
          netNegative ? "border-l-destructive" : "border-l-chart-4"
        )}
      >
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">{t("sim_result_title")}</CardTitle>
          <CardDescription className="text-xs">{result.combined_summary}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <div className="grid grid-cols-2 gap-2 rounded-lg bg-muted/50 p-3 text-sm">
            <div>
              <div className="text-[11px] uppercase text-muted-foreground">{t("sim_before")}</div>
              <div className="font-semibold">{formatVND(result.monthly_cashflow_before)}</div>
            </div>
            <div>
              <div className="text-[11px] uppercase text-muted-foreground">{t("sim_after")}</div>
              <div className={cn("font-semibold", netNegative && "text-destructive")}>
                {formatVND(net)}
              </div>
            </div>
          </div>
          {result.risk_flags.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {result.risk_flags.map((f) => (
                <Badge key={f} variant="destructive">
                  {f}
                </Badge>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-2">
        {result.entity_impacts.map((imp) => {
          const meta = ENTITY_META[imp.entity];
          const Icon = meta?.icon ?? Building2;
          const label = meta ? t(meta.labelKey) : imp.entity;
          const colorClass = meta?.colorClass ?? "text-primary";
          return (
            <Card key={imp.entity}>
              <CardContent className="flex flex-col gap-2 p-3">
                <div className="flex items-center gap-2">
                  <Icon className={cn("size-4", colorClass)} />
                  <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {label}
                  </span>
                </div>
                <p className="text-xs leading-snug text-foreground">{imp.summary}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
