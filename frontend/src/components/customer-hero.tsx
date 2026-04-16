"use client";

import { TrendingUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { formatVNDCompact } from "@/lib/format";

interface Props {
  name: string;
  monthlyIncome?: number;
  monthlySpending?: number;
}

/** Greeting card shown at the top of the Feed. Values fall back to placeholders
 *  when the backend summary isn't loaded yet. */
export function CustomerHero({ name, monthlyIncome, monthlySpending }: Props) {
  const net =
    monthlyIncome != null && monthlySpending != null ? monthlyIncome - monthlySpending : null;

  return (
    <Card className="overflow-hidden border-none bg-gradient-to-br from-primary via-primary to-chart-2 text-primary-foreground">
      <CardContent className="flex flex-col gap-4 p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-1">
            <span className="text-[11px] font-medium uppercase tracking-wider opacity-80">
              Xin chào
            </span>
            <h2 className="text-xl font-semibold leading-tight">{name}</h2>
          </div>
          <span className="flex size-9 items-center justify-center rounded-full bg-white/15 backdrop-blur">
            <TrendingUp className="size-4" />
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2 rounded-xl bg-white/10 p-3 text-sm backdrop-blur">
          <Stat label="Thu nhập" value={monthlyIncome != null ? formatVNDCompact(monthlyIncome) : "—"} />
          <Stat label="Chi tiêu" value={monthlySpending != null ? formatVNDCompact(monthlySpending) : "—"} />
          <Stat label="Còn lại" value={net != null ? formatVNDCompact(net) : "—"} accent={net != null && net < 0} />
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wider opacity-70">{label}</span>
      <span
        className={
          accent ? "text-sm font-semibold text-yellow-200" : "text-sm font-semibold"
        }
      >
        {value}
      </span>
    </div>
  );
}
