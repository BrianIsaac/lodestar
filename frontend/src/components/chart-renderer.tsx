"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  XAxis,
  YAxis,
} from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { formatVNDCompact } from "@/lib/format";
import type { ChartSpec } from "@/lib/types";

const COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];

interface Props {
  spec: ChartSpec;
  /** Compact rendering for feed card thumbnails. */
  compact?: boolean;
}

export function ChartRenderer({ spec, compact }: Props) {
  switch (spec.chart_type) {
    case "donut":
    case "pie":
      return <DonutChart spec={spec} compact={compact} />;
    case "bar":
    case "grouped_bar":
      return <BarChartView spec={spec} compact={compact} />;
    case "line":
      return <LineChartView spec={spec} compact={compact} />;
    case "waterfall":
      return <WaterfallChart spec={spec} compact={compact} />;
    case "progress":
      return <ProgressChart spec={spec} />;
    default:
      return (
        <p className="text-xs text-muted-foreground">
          Không hỗ trợ biểu đồ &quot;{spec.chart_type}&quot;
        </p>
      );
  }
}

function buildChartConfig(labels: string[]): ChartConfig {
  const config: ChartConfig = {};
  labels.forEach((label, i) => {
    config[label] = { label, color: COLORS[i % COLORS.length] };
  });
  return config;
}

function DonutChart({ spec, compact }: Props) {
  const labels = (spec.data.labels as string[]) ?? [];
  const values = (spec.data.values as number[]) ?? [];
  const data = labels.map((name, i) => ({ name, value: values[i] ?? 0 }));
  const config = buildChartConfig(labels);
  const size = compact ? "max-h-[120px]" : "max-h-[200px]";

  return (
    <ChartContainer config={config} className={cn("mx-auto aspect-square", size)}>
      <PieChart>
        <ChartTooltip content={<ChartTooltipContent hideLabel />} />
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={compact ? 32 : 50}
          strokeWidth={2}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
      </PieChart>
    </ChartContainer>
  );
}

function BarChartView({ spec, compact }: Props) {
  const labels = (spec.data.labels as string[]) ?? [];
  const values = (spec.data.values as number[]) ?? [];
  const data = labels.map((name, i) => ({ name, value: values[i] ?? 0 }));
  const config = buildChartConfig(labels);
  const minH = compact ? "min-h-[120px]" : "min-h-[200px]";

  return (
    <ChartContainer config={config} className={cn("w-full", minH)}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
        <YAxis
          tickFormatter={(v) => formatVNDCompact(v)}
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 11 }}
          width={40}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="value" radius={[6, 6, 0, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}

function LineChartView({ spec, compact }: Props) {
  const periods = (spec.data.periods as string[]) ?? [];
  const amounts = (spec.data.amounts as number[]) ?? [];
  const data = periods.map((period, i) => ({ period, amount: amounts[i] ?? 0 }));
  const config: ChartConfig = { amount: { label: "Số tiền", color: "var(--color-chart-1)" } };
  const minH = compact ? "min-h-[120px]" : "min-h-[200px]";

  return (
    <ChartContainer config={config} className={cn("w-full", minH)}>
      <LineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="period" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
        <YAxis
          tickFormatter={(v) => formatVNDCompact(v)}
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 11 }}
          width={40}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Line
          type="monotone"
          dataKey="amount"
          stroke="var(--color-chart-1)"
          strokeWidth={2.5}
          dot={{ r: 3, fill: "var(--color-chart-1)" }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ChartContainer>
  );
}

interface WaterfallStep {
  label: string;
  value: number;
  type: string;
}

interface WaterfallRow {
  name: string;
  base: number;
  value: number;
  type: string;
}

/** Precompute cumulative base offsets for each waterfall step so bars render
 *  as a true staircase. Pure function — no render-time mutation. */
function computeWaterfallRows(steps: WaterfallStep[]): WaterfallRow[] {
  return steps.reduce<{ rows: WaterfallRow[]; cum: number }>(
    (acc, s) => {
      if (s.type === "net") {
        acc.rows.push({ name: s.label, base: 0, value: Math.abs(s.value), type: s.type });
        return { rows: acc.rows, cum: s.value };
      }
      const start = s.value >= 0 ? acc.cum : acc.cum + s.value;
      acc.rows.push({
        name: s.label,
        base: start,
        value: Math.abs(s.value),
        type: s.type,
      });
      return { rows: acc.rows, cum: acc.cum + s.value };
    },
    { rows: [], cum: 0 }
  ).rows;
}

/**
 * True waterfall chart: each expense bar starts from the previous cumulative
 * value, creating the characteristic staircase pattern. Implemented via a
 * stacked bar chart with an invisible "base" segment per bar.
 */
function WaterfallChart({ spec, compact }: Props) {
  const steps = (spec.data.steps as WaterfallStep[]) ?? [];
  const data = computeWaterfallRows(steps);

  const colorFor = (type: string) =>
    type === "income"
      ? "var(--color-chart-4)"
      : type === "net"
        ? "var(--color-chart-1)"
        : "var(--color-chart-5)";

  const config: ChartConfig = {
    value: { label: "Giá trị", color: "var(--color-chart-1)" },
  };

  const minH = compact ? "min-h-[140px]" : "min-h-[220px]";

  return (
    <ChartContainer config={config} className={cn("w-full", minH)}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" className="stroke-border" />
        <XAxis
          dataKey="name"
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 10 }}
          interval={0}
          angle={-20}
          textAnchor="end"
          height={42}
        />
        <YAxis
          tickFormatter={(v) => formatVNDCompact(v)}
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 11 }}
          width={40}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="base" stackId="w" fill="transparent" />
        <Bar dataKey="value" stackId="w" radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => (
            <Cell key={i} fill={colorFor(entry.type)} />
          ))}
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}

function ProgressChart({ spec }: { spec: ChartSpec }) {
  const pct = Math.min(100, Math.max(0, (spec.data.progress_pct as number) ?? 0));
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{spec.title}</span>
        <span className="font-semibold text-primary">{pct.toFixed(0)}%</span>
      </div>
      <Progress value={pct} />
      {spec.summary && <p className="text-xs text-muted-foreground">{spec.summary}</p>}
    </div>
  );
}
