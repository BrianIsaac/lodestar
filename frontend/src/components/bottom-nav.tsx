"use client";

import type { LucideIcon } from "lucide-react";
import { Compass, Newspaper, Wallet } from "lucide-react";
import { cn } from "@/lib/utils";

export type TabValue = "feed" | "plan" | "products";

interface Props {
  value: TabValue;
  onChange: (value: TabValue) => void;
}

interface Item {
  value: TabValue;
  icon: LucideIcon;
  label: string;
}

const ITEMS: Item[] = [
  { value: "feed", icon: Newspaper, label: "Bảng tin" },
  { value: "plan", icon: Compass, label: "Kế hoạch" },
  { value: "products", icon: Wallet, label: "Sản phẩm" },
];

export function BottomNav({ value, onChange }: Props) {
  return (
    <nav
      aria-label="Điều hướng chính"
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
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
