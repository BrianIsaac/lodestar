"use client";

import { Monitor, Smartphone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";
import { useLayoutMode } from "@/lib/layout-mode";

export function LayoutToggle() {
  const { mode, toggle } = useLayoutMode();
  const { t } = useT();
  const isApp = mode === "app";

  // Icon shows the TARGET mode — click to switch to that view. Mirrors how
  // the theme toggle surfaces the "opposite" icon in its trigger button.
  return (
    <Button
      variant="ghost"
      size="icon-sm"
      aria-label={t("layout_toggle_aria")}
      onClick={toggle}
      title={isApp ? t("layout_web") : t("layout_app")}
    >
      {isApp ? <Monitor /> : <Smartphone />}
    </Button>
  );
}
