"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { InsightFeed } from "@/components/insight-feed";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { searchProducts } from "@/lib/api";
import type { ProductInfo } from "@/lib/types";

const CUSTOMER_ID = "C001";

function ProductSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ProductInfo[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSearch() {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const products = await searchProducts(query);
      setResults(products);
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
          handleSearch();
        }}
        className="flex gap-2"
      >
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Tìm sản phẩm... (vd: thẻ tín dụng, vay mua nhà)"
        />
        <Button type="submit" disabled={loading}>
          Tìm
        </Button>
      </form>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {results.map((p) => (
          <Card key={p.product_id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">{p.name_vi}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-1">
              <p className="text-xs text-muted-foreground">{p.description_vi}</p>
              <div className="flex gap-2">
                <Badge variant="outline">{p.entity}</Badge>
                <Badge variant="secondary">{p.product_type}</Badge>
                {p.interest_rate != null && (
                  <Badge variant="default">{p.interest_rate}%</Badge>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col gap-6 p-4 md:p-8">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-primary">
          Shinhan Financial Coach
        </h1>
        <p className="text-sm text-muted-foreground">
          SOL Vietnam — AI Personal Financial Coach
        </p>
      </header>

      <Tabs defaultValue="feed">
        <TabsList>
          <TabsTrigger value="feed">Insight Feed</TabsTrigger>
          <TabsTrigger value="goals">Goals</TabsTrigger>
          <TabsTrigger value="products">Products</TabsTrigger>
        </TabsList>

        <TabsContent value="feed" className="mt-4">
          <InsightFeed customerId={CUSTOMER_ID} />
        </TabsContent>

        <TabsContent value="goals" className="mt-4">
          <p className="text-muted-foreground">Goals view — coming soon.</p>
        </TabsContent>

        <TabsContent value="products" className="mt-4">
          <ProductSearch />
        </TabsContent>
      </Tabs>
    </div>
  );
}
