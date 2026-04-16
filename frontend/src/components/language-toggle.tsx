"use client";

import { Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useT } from "@/lib/i18n";

export function LanguageToggle() {
  const { lang, setLang, t } = useT();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={t("lang_aria")}
          >
            <Globe />
          </Button>
        }
      />
      <DropdownMenuContent align="end">
        <DropdownMenuCheckboxItem checked={lang === "vi"} onCheckedChange={() => setLang("vi")}>
          {t("lang_vi")}
        </DropdownMenuCheckboxItem>
        <DropdownMenuCheckboxItem checked={lang === "en"} onCheckedChange={() => setLang("en")}>
          {t("lang_en")}
        </DropdownMenuCheckboxItem>
        <DropdownMenuCheckboxItem checked={lang === "ko"} onCheckedChange={() => setLang("ko")}>
          {t("lang_ko")}
        </DropdownMenuCheckboxItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
