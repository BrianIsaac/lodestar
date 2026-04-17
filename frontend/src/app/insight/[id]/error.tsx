"use client";

import { useEffect } from "react";
import { AlertTriangle, ArrowLeft, RefreshCw } from "lucide-react";
import Link from "next/link";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/app-shell";
import { useT } from "@/lib/i18n";

export default function InsightError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { t } = useT();

  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <AppShell>
      <div className="flex flex-col gap-4 p-4">
        <Link href="/" className="inline-flex w-fit">
          <Button variant="ghost" size="sm" className="-ml-2">
            <ArrowLeft data-icon="inline-start" />
            {t("back_to_feed")}
          </Button>
        </Link>
        <Alert variant="destructive">
          <AlertTriangle />
          <AlertTitle>{t("error_boundary_title")}</AlertTitle>
          <AlertDescription>
            {t("error_boundary_body")}
            {error.digest ? (
              <span className="mt-2 block font-mono text-[10px] opacity-70">
                {error.digest}
              </span>
            ) : null}
          </AlertDescription>
        </Alert>
        <Button onClick={reset} variant="default" className="w-fit">
          <RefreshCw data-icon="inline-start" />
          {t("error_boundary_retry")}
        </Button>
      </div>
    </AppShell>
  );
}
