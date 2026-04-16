import type { LucideIcon } from "lucide-react";
import { AlertTriangle, Baby, Sparkles, Target, Wallet } from "lucide-react";
import type { StringKey } from "@/lib/i18n";

export type Severity = "life_event" | "anomaly" | "milestone" | "info" | "product";

interface SeverityMeta {
  icon: LucideIcon;
  labelKey: StringKey;
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
    labelKey: "sev_life_event",
    badgeVariant: "destructive",
    borderClass: "border-l-destructive",
    iconBgClass: "bg-destructive/10",
    iconColorClass: "text-destructive",
  },
  anomaly: {
    icon: AlertTriangle,
    labelKey: "sev_anomaly",
    badgeVariant: "default",
    borderClass: "border-l-primary",
    iconBgClass: "bg-primary/10",
    iconColorClass: "text-primary",
  },
  milestone: {
    icon: Target,
    labelKey: "sev_milestone",
    badgeVariant: "secondary",
    borderClass: "border-l-chart-4",
    iconBgClass: "bg-chart-4/10",
    iconColorClass: "text-chart-4",
  },
  info: {
    icon: Sparkles,
    labelKey: "sev_info",
    badgeVariant: "outline",
    borderClass: "border-l-accent",
    iconBgClass: "bg-accent/30",
    iconColorClass: "text-accent-foreground",
  },
  product: {
    icon: Wallet,
    labelKey: "sev_product",
    badgeVariant: "secondary",
    borderClass: "border-l-chart-2",
    iconBgClass: "bg-chart-2/10",
    iconColorClass: "text-chart-2",
  },
};

export function getSeverityMeta(severity: string): SeverityMeta {
  return SEVERITY_META[severity as Severity] ?? SEVERITY_META.info;
}
