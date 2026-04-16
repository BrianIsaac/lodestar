"use client";

import { useState } from "react";
import { Activity, Play } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { postDemoTransaction, type DemoTransactionPayload } from "@/lib/api";
import { useT } from "@/lib/i18n";

interface Props {
  customerId: string;
  onInjected?: () => void;
}

interface Preset {
  label: string;
  emoji: string;
  payload: DemoTransactionPayload;
  hint?: string;
}

function presetsFor(customerId: string): { group: string; items: Preset[] }[] {
  return [
    {
      group: "Everyday",
      items: [
        {
          emoji: "☕",
          label: "Highlands Coffee 85K",
          payload: {
            customer_id: customerId,
            merchant: "Highland Coffee",
            amount: -85_000,
            category: "food",
          },
        },
        {
          emoji: "🚗",
          label: "Grab 95K",
          payload: {
            customer_id: customerId,
            merchant: "Grab",
            amount: -95_000,
            category: "transport",
          },
        },
      ],
    },
    {
      group: "Life event — baby",
      items: [
        {
          emoji: "👶",
          label: "Kids Plaza 2.1M",
          hint: "1st baby-merchant",
          payload: {
            customer_id: customerId,
            merchant: "Kids Plaza",
            amount: -2_100_000,
            category: "shopping",
          },
        },
        {
          emoji: "👶",
          label: "Con Cưng 1.8M",
          hint: "2nd — should trigger life_event",
          payload: {
            customer_id: customerId,
            merchant: "Con Cưng",
            amount: -1_800_000,
            category: "shopping",
          },
        },
        {
          emoji: "🏥",
          label: "Bệnh viện Phụ sản 3.5M",
          hint: "3rd baby signal (reinforces)",
          payload: {
            customer_id: customerId,
            merchant: "Bệnh viện Phụ sản Hà Nội",
            amount: -3_500_000,
            category: "health",
          },
        },
      ],
    },
    {
      group: "Anomalies",
      items: [
        {
          emoji: "📺",
          label: "Netflix 660K (3× normal)",
          hint: "should trigger recurring_change",
          payload: {
            customer_id: customerId,
            merchant: "Netflix VN",
            amount: -660_000,
            category: "bills",
          },
        },
        {
          emoji: "💳",
          label: "FPT Shop 28M",
          hint: "big shopping spend",
          payload: {
            customer_id: customerId,
            merchant: "FPT Shop",
            amount: -28_000_000,
            category: "shopping",
          },
        },
      ],
    },
    {
      group: "Income + Home",
      items: [
        {
          emoji: "💰",
          label: "Salary credit 12.5M",
          hint: "should trigger payday",
          payload: {
            customer_id: customerId,
            merchant: "LUONG THANG",
            amount: 12_500_000,
            category: "salary",
          },
        },
        {
          emoji: "🏠",
          label: "Vinhomes deposit 50M",
          hint: "home purchase signal",
          payload: {
            customer_id: customerId,
            merchant: "Công ty BĐS Vinhomes",
            amount: -50_000_000,
            category: "bills",
          },
        },
      ],
    },
  ];
}

export function DemoPanel({ customerId, onInjected }: Props) {
  const [busy, setBusy] = useState(false);
  const [customMerchant, setCustomMerchant] = useState("");
  const [customAmount, setCustomAmount] = useState("");
  const [customCategory, setCustomCategory] = useState("shopping");
  const { t } = useT();

  async function inject(payload: DemoTransactionPayload) {
    setBusy(true);
    try {
      await postDemoTransaction(payload);
      toast.success(t("demo_toast_agent_reasoning", { merchant: payload.merchant }));
      onInjected?.();
    } catch {
      toast.error(t("demo_toast_error"));
    } finally {
      setBusy(false);
    }
  }

  async function submitCustom(e: React.FormEvent) {
    e.preventDefault();
    const amount = Number(customAmount);
    if (!customMerchant || Number.isNaN(amount) || amount === 0) return;
    await inject({
      customer_id: customerId,
      merchant: customMerchant,
      amount,
      category: customCategory,
    });
    setCustomMerchant("");
    setCustomAmount("");
  }

  return (
    <Sheet>
      <SheetTrigger
        render={
          <Button
            variant="default"
            size="sm"
            className="fixed bottom-24 right-4 z-50 shadow-lg md:bottom-6"
            aria-label={t("demo_open")}
          >
            <Activity data-icon="inline-start" />
            {t("demo_open")}
          </Button>
        }
      />
      <SheetContent side="right" className="flex w-full flex-col gap-4 sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{t("demo_panel_title")}</SheetTitle>
          <SheetDescription>{t("demo_panel_desc")}</SheetDescription>
        </SheetHeader>

        <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4">
          {presetsFor(customerId).map((group) => (
            <section key={group.group} className="flex flex-col gap-2">
              <h4 className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                {group.group}
              </h4>
              <div className="flex flex-col gap-1.5">
                {group.items.map((preset) => (
                  <button
                    key={preset.label}
                    type="button"
                    onClick={() => inject(preset.payload)}
                    disabled={busy}
                    className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background px-3 py-2 text-left text-sm font-medium transition-colors hover:border-primary/50 hover:bg-primary/5 disabled:opacity-50"
                  >
                    <span className="flex items-center gap-2">
                      <span className="text-base leading-none">{preset.emoji}</span>
                      <span>{preset.label}</span>
                    </span>
                    {preset.hint && (
                      <span className="text-[10px] text-muted-foreground">{preset.hint}</span>
                    )}
                  </button>
                ))}
              </div>
            </section>
          ))}

          <section className="flex flex-col gap-2">
            <h4 className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              {t("demo_custom_header")}
            </h4>
            <form onSubmit={submitCustom}>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="demo-merchant">{t("demo_field_merchant")}</FieldLabel>
                  <Input
                    id="demo-merchant"
                    value={customMerchant}
                    onChange={(e) => setCustomMerchant(e.target.value)}
                    placeholder="Shopee"
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="demo-amount">{t("demo_field_amount")}</FieldLabel>
                  <Input
                    id="demo-amount"
                    type="number"
                    value={customAmount}
                    onChange={(e) => setCustomAmount(e.target.value)}
                    placeholder="-450000"
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="demo-category">{t("demo_field_category")}</FieldLabel>
                  <Input
                    id="demo-category"
                    value={customCategory}
                    onChange={(e) => setCustomCategory(e.target.value)}
                    placeholder="shopping"
                  />
                </Field>
              </FieldGroup>
              <Button type="submit" disabled={busy} className="mt-3 w-full">
                <Play data-icon="inline-start" />
                {t("demo_inject")}
              </Button>
            </form>
          </section>
        </div>

        <SheetClose
          render={
            <Button variant="ghost" className="mx-4 mb-4">
              {t("demo_close")}
            </Button>
          }
        />
      </SheetContent>
    </Sheet>
  );
}
