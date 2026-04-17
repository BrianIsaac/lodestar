"use client";

import { useEffect, useRef, useState } from "react";
import { Search, Wallet } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { searchProducts } from "@/lib/api";
import { formatVNDCompact } from "@/lib/format";
import { useT, type StringKey } from "@/lib/i18n";
import { useLayoutMode } from "@/lib/layout-mode";
import type { ProductInfo } from "@/lib/types";

/** Suggestion keys — resolved per language via useT(). bge-m3 is multilingual
 *  so Vi/En/Ko queries all retrieve sensibly from the Vietnamese catalogue. */
const SUGGESTION_KEYS: StringKey[] = [
  "products_suggestion_credit",
  "products_suggestion_home_loan",
  "products_suggestion_life_insurance",
];

const ENTITY_LABEL_KEY: Record<string, StringKey> = {
  bank: "product_entity_bank",
  finance: "product_entity_finance",
  securities: "product_entity_securities",
  life: "product_entity_life",
};

interface ProductSearchProps {
  /** Optional search phrase coming from a feed card quick-prompt. When
   *  set, the component fires the search on mount. */
  initialQuery?: string;
}

export function ProductSearch({ initialQuery }: ProductSearchProps = {}) {
  const [query, setQuery] = useState(initialQuery ?? "");
  const [results, setResults] = useState<ProductInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const { lang, t } = useT();
  const { mode } = useLayoutMode();
  const resultsGridClass =
    mode === "web"
      ? "grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3"
      : "flex flex-col gap-2";

  const cancelledRef = useRef(false);

  async function run(text: string) {
    const q = text.trim();
    if (!q) return;
    setQuery(q);
    setLoading(true);
    setSearched(true);
    try {
      const list = await searchProducts(q, lang);
      if (cancelledRef.current) return;
      setResults(list);
    } catch {
      if (cancelledRef.current) return;
      toast.error(t("products_fetch_error"));
      setResults([]);
    } finally {
      if (!cancelledRef.current) setLoading(false);
    }
  }

  // Auto-run the search when initialQuery is provided (feed quick-prompt
  // cross-link). Runs only once per initialQuery value, and cancels any
  // in-flight fetch on unmount so setState-after-unmount cannot fire
  // under React 19 strict-mode double-invocation.
  useEffect(() => {
    cancelledRef.current = false;
    if (initialQuery && initialQuery.trim()) {
      run(initialQuery);
    }
    return () => {
      cancelledRef.current = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  return (
    <div className="flex flex-col gap-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          run(query);
        }}
        className="flex items-center gap-2 rounded-full border border-border bg-background p-1.5 shadow-sm"
      >
        <span className="pl-2">
          <Search className="size-4 text-muted-foreground" />
        </span>
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("products_search_placeholder")}
          className="flex-1 border-none bg-transparent text-sm focus-visible:ring-0"
          disabled={loading}
        />
        <Button type="submit" size="sm" disabled={loading || !query.trim()}>
          {loading ? <Spinner aria-label={t("products_search_button")} /> : t("products_search_button")}
        </Button>
      </form>

      {!searched && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTION_KEYS.map((key) => {
            const label = t(key);
            return (
              <button
                key={key}
                type="button"
                onClick={() => run(label)}
                className="rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium transition-colors hover:bg-muted"
              >
                {label}
              </button>
            );
          })}
        </div>
      )}

      {searched && !loading && results.length === 0 && (
        <Empty>
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <Wallet />
            </EmptyMedia>
            <EmptyTitle>{t("products_empty_title")}</EmptyTitle>
            <EmptyDescription>{t("products_empty_desc")}</EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}

      <div className={resultsGridClass}>
        {results.map((p) => {
          // Server projects `name` and `description` to the requested
          // locale; fall back to the per-locale fields for older payloads.
          const name =
            p.name ||
            (lang === "ko"
              ? p.name_ko || p.name_vi
              : lang === "en"
                ? p.name_en || p.name_vi
                : p.name_vi);
          const description =
            p.description ||
            (lang === "ko"
              ? p.description_ko || p.description_vi
              : lang === "en"
                ? p.description_en || p.description_vi
                : p.description_vi);
          const entityKey = ENTITY_LABEL_KEY[p.entity];
          return (
            <Card key={p.product_id}>
              <CardContent className="flex flex-col gap-2 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex min-w-0 flex-col">
                    <span className="text-sm font-semibold leading-tight">{name}</span>
                    {description && (
                      <span className="text-xs text-muted-foreground">{description}</span>
                    )}
                  </div>
                  {p.interest_rate != null && (
                    <Badge variant="default" className="shrink-0">
                      {p.interest_rate}%
                    </Badge>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                  <Badge variant="secondary">
                    {entityKey ? t(entityKey) : p.entity}
                  </Badge>
                  <Badge variant="outline">{p.product_type}</Badge>
                  {p.min_income != null && p.min_income > 0 && (
                    <span className="text-muted-foreground">
                      {t("products_min_income")} {formatVNDCompact(p.min_income)}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
