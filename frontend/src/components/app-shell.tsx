"use client";

import Link from "next/link";
import { Compass } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/theme-toggle";
import { LanguageToggle } from "@/components/language-toggle";
import { LayoutToggle } from "@/components/layout-toggle";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";
import { useLayoutMode } from "@/lib/layout-mode";

interface Props {
  children: React.ReactNode;
  customerInitials?: string;
}

export function AppShell({ children, customerInitials = "KH" }: Props) {
  const { t } = useT();
  const { mode } = useLayoutMode();
  const containerClass = mode === "app" ? "max-w-md" : "max-w-6xl";
  const mainClass = mode === "app" ? "pb-24" : "pb-10";

  return (
    <div className="min-h-dvh bg-background">
      <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className={cn("mx-auto flex items-center justify-between gap-3 px-4 py-3", containerClass)}>
          <Link href="/" className="flex items-center gap-2">
            <span className="flex size-8 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <Compass className="size-4" />
            </span>
            <span className="flex flex-col leading-tight">
              <span className="text-sm font-semibold tracking-tight">Lodestar</span>
              <span className="text-[10px] font-medium text-muted-foreground">
                {t("brand_subtitle")}
              </span>
            </span>
          </Link>
          <div className="flex items-center gap-1">
            <LayoutToggle />
            <LanguageToggle />
            <ThemeToggle />
            <Avatar className="ml-1 size-8">
              <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
                {customerInitials}
              </AvatarFallback>
            </Avatar>
          </div>
        </div>
        <PoweredByQwen label={t("powered_by")} containerClass={containerClass} />
      </header>
      <main className={cn("mx-auto px-4 pt-4", containerClass, mainClass)}>{children}</main>
    </div>
  );
}

function PoweredByQwen({ label, containerClass }: { label: string; containerClass: string }) {
  return (
    <div className="border-t border-border/40 bg-background/60">
      <div className={cn("mx-auto flex items-center justify-center gap-1.5 px-4 py-1 text-[10px] text-muted-foreground", containerClass)}>
        <span className="flex size-3 items-center justify-center rounded-sm bg-primary/10 font-bold text-primary">
          Q
        </span>
        <span>
          {label}{" "}
          <span className="font-semibold text-foreground">Qwen</span>{" "}
          <span className="text-muted-foreground/70">· Alibaba Cloud</span>
        </span>
      </div>
    </div>
  );
}
