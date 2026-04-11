"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ChartRenderer } from "@/components/chart-renderer";
import { sendChat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

interface Props {
  insightId: string;
  customerId: string;
  initialContext?: string;
}

export function DrillDownChat({ insightId, customerId, initialContext }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSend() {
    if (!input.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendChat(insightId, customerId, input, initialContext);
      setMessages((prev) => [...prev, response.message]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Xin lỗi, đã xảy ra lỗi. Vui lòng thử lại." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-1 flex-col gap-3 overflow-y-auto">
        {messages.map((msg, i) => (
          <Card
            key={i}
            className={
              msg.role === "user"
                ? "ml-auto max-w-[80%] bg-primary text-primary-foreground"
                : "mr-auto max-w-[80%]"
            }
          >
            <CardContent className="flex flex-col gap-2 p-3">
              <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
              {msg.chart_spec && <ChartRenderer spec={msg.chart_spec} />}
            </CardContent>
          </Card>
        ))}
        {loading && (
          <Card className="mr-auto max-w-[80%]">
            <CardContent className="p-3">
              <div className="flex gap-1">
                <div className="size-2 animate-pulse rounded-full bg-muted-foreground" />
                <div className="size-2 animate-pulse rounded-full bg-muted-foreground delay-100" />
                <div className="size-2 animate-pulse rounded-full bg-muted-foreground delay-200" />
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex gap-2"
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Hỏi về tài chính của bạn..."
          disabled={loading}
        />
        <Button type="submit" disabled={loading || !input.trim()}>
          Gửi
        </Button>
      </form>
    </div>
  );
}
