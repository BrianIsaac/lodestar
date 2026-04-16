"use client";

import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { ChartRenderer } from "@/components/chart-renderer";
import { sendChat } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";
import type { ChatMessage } from "@/lib/types";

interface Props {
  insightId: string;
  customerId: string;
  initialContext?: string;
  suggestedPrompts?: string[];
}

/** Suggestion chips stay in Vietnamese across languages: the Coach LLM is
 *  tuned to respond in Vietnamese, so we keep the prompts it understands
 *  best even when the surrounding chrome is English. */
const DEFAULT_PROMPTS = [
  "Tôi nên làm gì tiếp theo?",
  "Nếu tôi mua nhà 2 tỷ thì sao?",
  "Có sản phẩm nào phù hợp không?",
];

export function DrillDownChat({
  insightId,
  customerId,
  initialContext,
  suggestedPrompts = DEFAULT_PROMPTS,
}: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [followups, setFollowups] = useState<string[]>(suggestedPrompts);
  const scrollAnchor = useRef<HTMLDivElement>(null);
  const { lang, t } = useT();

  useEffect(() => {
    scrollAnchor.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  async function submit(text: string) {
    const content = text.trim();
    if (!content || loading) return;

    const userMsg: ChatMessage = { role: "user", content, chart_spec: null };
    setMessages((xs) => [...xs, userMsg]);
    setInput("");
    setLoading(true);
    setFollowups([]);

    try {
      const resp = await sendChat(insightId, customerId, content, initialContext, lang);
      setMessages((xs) => [...xs, resp.message]);
      if (resp.suggested_followups?.length) {
        setFollowups(resp.suggested_followups);
      }
    } catch {
      setMessages((xs) => [
        ...xs,
        {
          role: "assistant",
          content: t("chat_error"),
          chart_spec: null,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3">
        {messages.length === 0 && !loading && (
          <div className="rounded-xl border border-dashed border-border bg-muted/30 p-4 text-center text-sm text-muted-foreground">
            {t("chat_empty_prompt")}
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {loading && (
          <div className="mr-auto flex max-w-[85%] items-center gap-2 rounded-2xl rounded-bl-sm border border-border bg-card px-4 py-3 text-sm text-muted-foreground">
            <Spinner className="size-4 text-primary" />
            <span>{t("chat_thinking")}</span>
          </div>
        )}
        <div ref={scrollAnchor} />
      </div>

      {followups.length > 0 && !loading && (
        <div className="flex flex-wrap gap-2">
          {followups.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => submit(prompt)}
              className="rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      <form
        className="flex items-center gap-2 rounded-full border border-border bg-background p-1.5 shadow-sm"
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("chat_placeholder")}
          className="flex-1 border-none bg-transparent text-sm focus-visible:ring-0"
          disabled={loading}
        />
        <Button
          type="submit"
          size="icon-sm"
          aria-label={t("chat_send_aria")}
          disabled={loading || !input.trim()}
        >
          <Send />
        </Button>
      </form>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div
      className={cn(
        "flex max-w-[85%] flex-col gap-2 rounded-2xl border px-4 py-3 text-sm leading-relaxed",
        isUser
          ? "ml-auto rounded-br-sm border-primary bg-primary text-primary-foreground"
          : "mr-auto rounded-bl-sm border-border bg-card text-card-foreground"
      )}
    >
      <div className="whitespace-pre-wrap">{message.content}</div>
      {message.chart_spec && (
        <div className="rounded-lg border border-border/70 bg-background p-2 text-foreground">
          <ChartRenderer spec={message.chart_spec} />
        </div>
      )}
    </div>
  );
}
