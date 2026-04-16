"use client";

import { useState } from "react";
import { Search, Wallet } from "lucide-react";
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
import type { ProductInfo } from "@/lib/types";

const ENTITY_LABEL: Record<string, string> = {
  bank: "Ngân hàng",
  finance: "Tài chính",
  securities: "Chứng khoán",
  life: "Bảo hiểm",
};

const SUGGESTIONS = [
  "thẻ tín dụng cho lương 10 triệu",
  "vay mua nhà",
  "bảo hiểm nhân thọ",
];

export function ProductSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ProductInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function run(text: string) {
    const q = text.trim();
    if (!q) return;
    setQuery(q);
    setLoading(true);
    setSearched(true);
    try {
      const list = await searchProducts(q);
      setResults(list);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

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
          placeholder="Tìm sản phẩm bằng tiếng Việt…"
          className="flex-1 border-none bg-transparent text-sm focus-visible:ring-0"
          disabled={loading}
        />
        <Button type="submit" size="sm" disabled={loading || !query.trim()}>
          {loading ? <Spinner /> : "Tìm"}
        </Button>
      </form>

      {!searched && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => run(s)}
              className="rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium transition-colors hover:bg-muted"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {searched && !loading && results.length === 0 && (
        <Empty>
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <Wallet />
            </EmptyMedia>
            <EmptyTitle>Không tìm thấy sản phẩm</EmptyTitle>
            <EmptyDescription>Thử từ khoá khác như &quot;thẻ tín dụng&quot; hoặc &quot;vay mua nhà&quot;.</EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}

      <div className="flex flex-col gap-2">
        {results.map((p) => (
          <Card key={p.product_id}>
            <CardContent className="flex flex-col gap-2 p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex min-w-0 flex-col">
                  <span className="text-sm font-semibold leading-tight">{p.name_vi}</span>
                  {p.description_vi && (
                    <span className="text-xs text-muted-foreground">{p.description_vi}</span>
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
                  {ENTITY_LABEL[p.entity] ?? p.entity}
                </Badge>
                <Badge variant="outline">{p.product_type}</Badge>
                {p.min_income != null && p.min_income > 0 && (
                  <span className="text-muted-foreground">
                    Thu nhập tối thiểu {formatVNDCompact(p.min_income)}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
