import type { LucideIcon } from "lucide-react";
import { AlertTriangle, Baby, Target, Sparkles, Wallet } from "lucide-react";

export type Severity = "life_event" | "anomaly" | "milestone" | "info" | "product";

interface SeverityMeta {
  icon: LucideIcon;
  labelVi: string;
  badgeVariant: "default" | "secondary" | "destructive" | "outline";
  /** Tailwind classes for the card's left-border accent. */
  borderClass: string;
  /** Tailwind classes for the icon background chip. */
  iconBgClass: string;
  iconColorClass: string;
}

export const SEVERITY_META: Record<Severity, SeverityMeta> = {
  life_event: {
    icon: Baby,
    labelVi: "Sự kiện cuộc sống",
    badgeVariant: "destructive",
    borderClass: "border-l-destructive",
    iconBgClass: "bg-destructive/10",
    iconColorClass: "text-destructive",
  },
  anomaly: {
    icon: AlertTriangle,
    labelVi: "Bất thường",
    badgeVariant: "default",
    borderClass: "border-l-primary",
    iconBgClass: "bg-primary/10",
    iconColorClass: "text-primary",
  },
  milestone: {
    icon: Target,
    labelVi: "Mốc quan trọng",
    badgeVariant: "secondary",
    borderClass: "border-l-chart-4",
    iconBgClass: "bg-chart-4/10",
    iconColorClass: "text-chart-4",
  },
  info: {
    icon: Sparkles,
    labelVi: "Thông tin",
    badgeVariant: "outline",
    borderClass: "border-l-accent",
    iconBgClass: "bg-accent/30",
    iconColorClass: "text-accent-foreground",
  },
  product: {
    icon: Wallet,
    labelVi: "Sản phẩm",
    badgeVariant: "secondary",
    borderClass: "border-l-chart-2",
    iconBgClass: "bg-chart-2/10",
    iconColorClass: "text-chart-2",
  },
};

export function getSeverityMeta(severity: string): SeverityMeta {
  return SEVERITY_META[severity as Severity] ?? SEVERITY_META.info;
}
