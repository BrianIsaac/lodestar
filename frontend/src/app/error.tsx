"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";

export default function RootError({
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
    <div className="flex min-h-dvh items-center justify-center p-6">
      <div className="flex max-w-md flex-col gap-4">
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
        <Button onClick={reset} variant="default">
          <RefreshCw data-icon="inline-start" />
          {t("error_boundary_retry")}
        </Button>
      </div>
    </div>
  );
}
