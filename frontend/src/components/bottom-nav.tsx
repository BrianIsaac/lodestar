"use client";

import type { LucideIcon } from "lucide-react";
import { Compass, Newspaper, Wallet } from "lucide-react";
import { cn } from "@/lib/utils";
import { useT, type StringKey } from "@/lib/i18n";
import { useLayoutMode } from "@/lib/layout-mode";

export type TabValue = "feed" | "plan" | "products";

interface Props {
  value: TabValue;
  onChange: (value: TabValue) => void;
}

interface Item {
  value: TabValue;
  icon: LucideIcon;
  labelKey: StringKey;
}

const ITEMS: Item[] = [
  { value: "feed", icon: Newspaper, labelKey: "tab_feed" },
  { value: "plan", icon: Compass, labelKey: "tab_plan" },
  { value: "products", icon: Wallet, labelKey: "tab_products" },
];

/** Fixed bottom tab bar for app (phone) layout. Hidden in web layout —
 *  `TopNavTabs` renders the same items inline at the top of main content. */
export function BottomNav({ value, onChange }: Props) {
  const { t } = useT();
  const { mode } = useLayoutMode();

  if (mode !== "app") return null;

  return (
    <nav
      aria-label={t("nav_aria")}
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border/60 bg-background/90 backdrop-blur supports-[backdrop-filter]:bg-background/70"
    >
      <div className="mx-auto flex max-w-md items-stretch justify-around px-2 pt-1 pb-[calc(env(safe-area-inset-bottom)+0.5rem)]">
        {ITEMS.map((item) => {
          const active = item.value === value;
          const Icon = item.icon;
          return (
            <button
              key={item.value}
              type="button"
              onClick={() => onChange(item.value)}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex flex-1 flex-col items-center gap-0.5 rounded-xl px-2 py-2 text-[11px] font-medium transition-colors",
                active ? "text-primary" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className={cn("size-5 transition-transform", active && "scale-110")} />
              <span>{t(item.labelKey)}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

/** Inline tab bar shown at the top of main content in web layout.
 *  Mirrors BottomNav items so behaviour stays identical across modes. */
export function TopNavTabs({ value, onChange }: Props) {
  const { t } = useT();
  const { mode } = useLayoutMode();

  if (mode !== "web") return null;

  return (
    <nav
      aria-label={t("nav_aria")}
      className="-mx-4 mb-4 flex items-stretch gap-1 border-b border-border/60 px-4"
    >
      {ITEMS.map((item) => {
        const active = item.value === value;
        const Icon = item.icon;
        return (
          <button
            key={item.value}
            type="button"
            onClick={() => onChange(item.value)}
            aria-current={active ? "page" : undefined}
            className={cn(
              "-mb-px flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors",
              active
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            <Icon className="size-4" />
            {t(item.labelKey)}
          </button>
        );
      })}
    </nav>
  );
}
