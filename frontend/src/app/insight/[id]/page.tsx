"use client";

import { use } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { DrillDownChat } from "@/components/drill-down-chat";

const CUSTOMER_ID = "C001";

export default function InsightPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  return (
    <div className="flex min-h-screen flex-col gap-4 p-4 md:p-8">
      <div className="flex items-center gap-2">
        <Link href="/">
          <Button variant="outline" size="sm">
            ← Back
          </Button>
        </Link>
        <h1 className="text-lg font-semibold text-primary">Insight Detail</h1>
      </div>

      <Separator />

      <div className="flex-1">
        <DrillDownChat
          insightId={id}
          customerId={CUSTOMER_ID}
          initialContext={`Insight ID: ${id}`}
        />
      </div>
    </div>
  );
}
