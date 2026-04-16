"use client";

import { useEffect, useState } from "react";
import {
  Coffee,
  Car,
  ShoppingBag,
  Receipt,
  HeartPulse,
  GraduationCap,
  Wallet,
  Tv,
  ArrowDownLeft,
  ArrowUpRight,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { formatVNDCompact } from "@/lib/format";
import { fetchRecentTransactions, type RecentTransaction } from "@/lib/api";
import { useT } from "@/lib/i18n";

interface Props {
  customerId: string;
  /** Incremented by the parent on every demo-transaction submission.
   *  A change triggers a refetch so the list reflects the new activity. */
  refreshKey?: number;
  limit?: number;
}

const CATEGORY_ICON: Record<string, typeof Coffee> = {
  food: Coffee,
  transport: Car,
  shopping: ShoppingBag,
  bills: Receipt,
  health: HeartPulse,
  education: GraduationCap,
  salary: Wallet,
  entertainment: Tv,
};

export function RecentTransactions({ customerId, refreshKey = 0, limit = 8 }: Props) {
  const [txns, setTxns] = useState<RecentTransaction[] | null>(null);
  const { t } = useT();
  const [flashId, setFlashId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchRecentTransactions(customerId, limit)
      .then((list) => {
        if (cancelled) return;
        setTxns(list);
        if (refreshKey > 0 && list.length > 0) {
          setFlashId(list[0].transaction_id);
          const handle = setTimeout(() => setFlashId(null), 2500);
          return () => clearTimeout(handle);
        }
      })
      .catch(() => {
        if (!cancelled) setTxns([]);
      });
    return () => {
      cancelled = true;
    };
  }, [customerId, refreshKey, limit]);

  return (
    <Card>
      <CardContent className="flex flex-col gap-2 p-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            {t("recent_transactions")}
          </span>
          <span className="text-[10px] text-muted-foreground/70">
            {txns ? `${txns.length}` : "—"}
          </span>
        </div>
        {txns === null ? (
          <div className="flex flex-col gap-1.5">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full rounded-md" />
            ))}
          </div>
        ) : txns.length === 0 ? (
          <p className="py-2 text-center text-xs text-muted-foreground">
            {t("recent_transactions_empty")}
          </p>
        ) : (
          <ul className="flex flex-col gap-1">
            {txns.map((tx) => {
              const Icon = CATEGORY_ICON[tx.category] ?? ShoppingBag;
              const isInflow = tx.amount > 0;
              const DirIcon = isInflow ? ArrowDownLeft : ArrowUpRight;
              return (
                <li
                  key={tx.transaction_id}
                  className={cn(
                    "flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-xs transition-colors",
                    flashId === tx.transaction_id && "animate-in fade-in bg-primary/10 ring-1 ring-primary/40"
                  )}
                >
                  <div className="flex min-w-0 items-center gap-2">
                    <span className="flex size-6 shrink-0 items-center justify-center rounded-md bg-muted">
                      <Icon className="size-3.5 text-muted-foreground" />
                    </span>
                    <div className="flex min-w-0 flex-col leading-tight">
                      <span className="truncate font-medium">{tx.merchant || tx.category}</span>
                      <span className="text-[10px] text-muted-foreground">{tx.date}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <DirIcon
                      className={cn(
                        "size-3",
                        isInflow ? "text-chart-4" : "text-muted-foreground"
                      )}
                    />
                    <span
                      className={cn(
                        "tabular-nums font-medium",
                        isInflow ? "text-chart-4" : "text-foreground"
                      )}
                    >
                      {formatVNDCompact(tx.amount)}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
