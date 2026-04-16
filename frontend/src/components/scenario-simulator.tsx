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
import type { ScenarioResult } from "@/lib/types";

interface Props {
  customerId: string;
}

const ENTITY_META: Record<string, { icon: LucideIcon; labelVi: string; colorClass: string }> = {
  bank: { icon: Building2, labelVi: "Ngân hàng", colorClass: "text-chart-1" },
  finance: { icon: PiggyBank, labelVi: "Tài chính tiêu dùng", colorClass: "text-chart-2" },
  securities: { icon: TrendingUp, labelVi: "Chứng khoán", colorClass: "text-chart-4" },
  life: { icon: Shield, labelVi: "Bảo hiểm nhân thọ", colorClass: "text-chart-5" },
};

export function ScenarioSimulator({ customerId }: Props) {
  const [price, setPrice] = useState("2000000000");
  const [down, setDown] = useState("0.2");
  const [term, setTerm] = useState("240");
  const [rate, setRate] = useState("7.5");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await simulateScenario(customerId, "home_purchase", {
        property_price: Number(price),
        down_payment_pct: Number(down),
        loan_term_months: Number(term),
        interest_rate: Number(rate),
      });
      setResult(res);
    } catch {
      setError("Mô phỏng thất bại. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Nếu tôi mua nhà…</CardTitle>
          <CardDescription className="text-xs">
            Lodestar mô phỏng tác động trên cả bốn đơn vị Shinhan.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={run}>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="sim-price">Giá nhà (VND)</FieldLabel>
                <Input
                  id="sim-price"
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  min={0}
                />
                <FieldDescription>Ví dụ 2,000,000,000 cho nhà 2 tỷ.</FieldDescription>
              </Field>
              <div className="grid grid-cols-3 gap-3">
                <Field>
                  <FieldLabel htmlFor="sim-down">Tỷ lệ đặt cọc</FieldLabel>
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
                  <FieldLabel htmlFor="sim-term">Kỳ (tháng)</FieldLabel>
                  <Input
                    id="sim-term"
                    type="number"
                    value={term}
                    onChange={(e) => setTerm(e.target.value)}
                    min={12}
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="sim-rate">Lãi (%)</FieldLabel>
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
            </FieldGroup>
            <Button type="submit" disabled={loading} className="mt-4 w-full">
              {loading ? (
                <>
                  <Spinner data-icon="inline-start" />
                  Đang mô phỏng…
                </>
              ) : (
                <>
                  <PlayCircle data-icon="inline-start" />
                  Chạy mô phỏng
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Lỗi</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {result && <ScenarioResultView result={result} />}
    </div>
  );
}

function ScenarioResultView({ result }: { result: ScenarioResult }) {
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
          <CardTitle className="text-sm">Kết quả tổng hợp</CardTitle>
          <CardDescription className="text-xs">{result.combined_summary}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <div className="grid grid-cols-2 gap-2 rounded-lg bg-muted/50 p-3 text-sm">
            <div>
              <div className="text-[11px] uppercase text-muted-foreground">Trước</div>
              <div className="font-semibold">{formatVND(result.monthly_cashflow_before)}</div>
            </div>
            <div>
              <div className="text-[11px] uppercase text-muted-foreground">Sau</div>
              <div className={cn("font-semibold", netNegative && "text-destructive")}>
                {formatVND(net)}
              </div>
            </div>
          </div>
          {result.risk_flags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {result.risk_flags.map((f) => (
                <Badge key={f} variant="destructive">
                  {f}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-2">
        {result.entity_impacts.map((imp) => {
          const meta = ENTITY_META[imp.entity] ?? {
            icon: Building2,
            labelVi: imp.entity,
            colorClass: "text-primary",
          };
          const Icon = meta.icon;
          return (
            <Card key={imp.entity}>
              <CardContent className="flex flex-col gap-2 p-3">
                <div className="flex items-center gap-2">
                  <Icon className={cn("size-4", meta.colorClass)} />
                  <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {meta.labelVi}
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
