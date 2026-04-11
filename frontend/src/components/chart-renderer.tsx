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
import type { ChartSpec } from "@/lib/types";

const COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];

function formatVND(value: number): string {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(value);
}

function buildChartConfig(labels: string[]): ChartConfig {
  const config: ChartConfig = {};
  labels.forEach((label, i) => {
    config[label] = {
      label,
      color: COLORS[i % COLORS.length],
    };
  });
  return config;
}

function DonutChart({ spec }: { spec: ChartSpec }) {
  const labels = (spec.data.labels as string[]) ?? [];
  const values = (spec.data.values as number[]) ?? [];
  const data = labels.map((name, i) => ({ name, value: values[i] ?? 0 }));
  const config = buildChartConfig(labels);

  return (
    <ChartContainer config={config} className="mx-auto aspect-square max-h-[200px]">
      <PieChart>
        <ChartTooltip content={<ChartTooltipContent />} />
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={50}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
      </PieChart>
    </ChartContainer>
  );
}

function BarChartView({ spec }: { spec: ChartSpec }) {
  const labels = (spec.data.labels as string[]) ?? [];
  const values = (spec.data.values as number[]) ?? [];
  const data = labels.map((name, i) => ({ name, value: values[i] ?? 0 }));
  const config = buildChartConfig(labels);

  return (
    <ChartContainer config={config} className="min-h-[200px] w-full">
      <BarChart data={data}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="name" tickLine={false} axisLine={false} />
        <YAxis tickFormatter={(v) => formatVND(v)} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="value" fill="var(--color-chart-1)" radius={4} />
      </BarChart>
    </ChartContainer>
  );
}

function LineChartView({ spec }: { spec: ChartSpec }) {
  const periods = (spec.data.periods as string[]) ?? [];
  const amounts = (spec.data.amounts as number[]) ?? [];
  const data = periods.map((period, i) => ({ period, amount: amounts[i] ?? 0 }));
  const config: ChartConfig = { amount: { label: "Amount", color: "var(--color-chart-1)" } };

  return (
    <ChartContainer config={config} className="min-h-[200px] w-full">
      <LineChart data={data}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="period" tickLine={false} axisLine={false} />
        <YAxis tickFormatter={(v) => formatVND(v)} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Line type="monotone" dataKey="amount" stroke="var(--color-chart-1)" strokeWidth={2} />
      </LineChart>
    </ChartContainer>
  );
}

function WaterfallChart({ spec }: { spec: ChartSpec }) {
  const steps = (spec.data.steps as Array<{ label: string; value: number; type: string }>) ?? [];
  const data = steps.map((s) => ({
    name: s.label,
    value: Math.abs(s.value),
    fill: s.type === "income" ? "var(--color-chart-1)" : s.type === "net" ? "var(--color-chart-3)" : "var(--color-chart-5)",
  }));
  const config: ChartConfig = { value: { label: "Amount", color: "var(--color-chart-1)" } };

  return (
    <ChartContainer config={config} className="min-h-[200px] w-full">
      <BarChart data={data}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="name" tickLine={false} axisLine={false} />
        <YAxis tickFormatter={(v) => formatVND(v)} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="value" radius={4}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}

function ProgressChart({ spec }: { spec: ChartSpec }) {
  const pct = (spec.data.progress_pct as number) ?? 0;
  return (
    <div className="flex flex-col gap-2">
      <div className="flex justify-between text-sm">
        <span>{spec.title}</span>
        <span className="font-semibold">{pct.toFixed(0)}%</span>
      </div>
      <div className="h-3 w-full rounded-full bg-muted">
        <div
          className="h-3 rounded-full bg-primary transition-all"
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
      {spec.summary && <p className="text-xs text-muted-foreground">{spec.summary}</p>}
    </div>
  );
}

export function ChartRenderer({ spec }: { spec: ChartSpec }) {
  switch (spec.chart_type) {
    case "donut":
    case "pie":
      return <DonutChart spec={spec} />;
    case "bar":
    case "grouped_bar":
      return <BarChartView spec={spec} />;
    case "line":
      return <LineChartView spec={spec} />;
    case "waterfall":
      return <WaterfallChart spec={spec} />;
    case "progress":
      return <ProgressChart spec={spec} />;
    default:
      return <p className="text-sm text-muted-foreground">Chart type &quot;{spec.chart_type}&quot; not supported</p>;
  }
}
