"use client";

import { Monitor, Smartphone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";
import { useLayoutMode } from "@/lib/layout-mode";

export function LayoutToggle() {
  const { mode, toggle } = useLayoutMode();
  const { t } = useT();
  const isApp = mode === "app";

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      aria-label={t("layout_toggle_aria")}
      onClick={toggle}
      title={isApp ? t("layout_app") : t("layout_web")}
    >
      {isApp ? <Smartphone /> : <Monitor />}
    </Button>
  );
}
