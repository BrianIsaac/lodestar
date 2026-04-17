"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Send, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { ChartRenderer } from "@/components/chart-renderer";
import { fetchChatHistory, sendChat } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useT, type Lang, type StringKey } from "@/lib/i18n";
import type { ChatMessage } from "@/lib/types";

interface Props {
  insightId: string;
  customerId: string;
  initialContext?: string;
  /** Optional override. Falls back to language-aware defaults built from the
   *  chat_prompt_* i18n keys. */
  suggestedPrompts?: string[];
}

const DEFAULT_PROMPT_KEYS: StringKey[] = [
  "chat_prompt_next",
  "chat_prompt_scenario",
  "chat_prompt_product",
];

export function DrillDownChat({
  insightId,
  customerId,
  initialContext,
  suggestedPrompts,
}: Props) {
  const { lang, t } = useT();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  // Tri-lingual chip bundle kept in plain state so a language toggle
  // re-derives the displayed chips via `bundle[lang]`. Stored as the
  // whole dict instead of a flat list so the toggle is free — no round
  // trip to the backend.
  const [followupsI18n, setFollowupsI18n] =
    useState<Record<string, string[]> | null>(null);
  const scrollAnchor = useRef<HTMLDivElement>(null);

  const searchParams = useSearchParams();
  const prefillPrompt = searchParams.get("q");

  useEffect(() => {
    scrollAnchor.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  // Restore prior turns from the interaction ledger on mount so
  // navigating away and back preserves the thread. The component's
  // message list is otherwise pure React state and would be lost.
  useEffect(() => {
    let cancelled = false;
    fetchChatHistory(insightId)
      .then((msgs) => {
        if (cancelled) return;
        setMessages(msgs);
      })
      .catch(() => {
        // Silent — empty history is the correct degraded state.
      })
      .finally(() => {
        if (!cancelled) setHistoryLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, [insightId]);

  // Auto-submit a quick-prompt coming from a feed card chip. Runs once
  // per URL, only after history has loaded and only when history is
  // empty — a restored thread means the prefill already ran on a
  // previous visit and re-firing it would duplicate the question.
  const submittedPrefillRef = useRef<string | null>(null);
  useEffect(() => {
    if (!historyLoaded) return;
    if (!prefillPrompt) return;
    if (submittedPrefillRef.current === prefillPrompt) return;
    if (messages.length > 0) {
      submittedPrefillRef.current = prefillPrompt;
      return;
    }
    submittedPrefillRef.current = prefillPrompt;
    submit(prefillPrompt);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillPrompt, historyLoaded, messages.length]);

  async function submit(text: string) {
    const content = text.trim();
    if (!content || loading) return;

    const userMsg: ChatMessage = { role: "user", content, chart_spec: null };
    setMessages((xs) => [...xs, userMsg]);
    setInput("");
    setLoading(true);
    setFollowupsI18n(null);

    try {
      const resp = await sendChat(insightId, customerId, content, initialContext, lang);
      const toolChips: ChatMessage[] = (resp.tool_calls ?? []).map((name) => ({
        role: "tool",
        content: name,
        chart_spec: null,
      }));
      setMessages((xs) => [...xs, ...toolChips, resp.message]);
      if (resp.suggested_followups_i18n) {
        setFollowupsI18n(resp.suggested_followups_i18n);
      } else if (resp.suggested_followups?.length) {
        // Older backend shape: wrap the single-locale chips so the
        // render path below keeps working without a type split.
        setFollowupsI18n({ [lang]: resp.suggested_followups });
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

  const defaultFollowups = suggestedPrompts ?? DEFAULT_PROMPT_KEYS.map((k) => t(k));
  const activeFollowups: string[] = (() => {
    if (!followupsI18n) return messages.length === 0 ? defaultFollowups : [];
    return followupsI18n[lang] ?? followupsI18n.vi ?? defaultFollowups;
  })();

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3">
        {messages.length === 0 && !loading ? (
          <div className="rounded-xl border border-dashed border-border bg-muted/30 p-4 text-center text-sm text-muted-foreground">
            {t("chat_empty_prompt")}
          </div>
        ) : null}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} lang={lang} />
        ))}

        {loading ? (
          <div className="mr-auto flex max-w-[85%] items-center gap-2 rounded-2xl rounded-bl-sm border border-border bg-card px-4 py-3 text-sm text-muted-foreground">
            <Spinner className="size-4 text-primary" aria-label={t("chat_thinking")} />
            <span>{t("chat_thinking")}</span>
          </div>
        ) : null}
        <div ref={scrollAnchor} />
      </div>

      {activeFollowups.length > 0 && !loading ? (
        <div className="flex flex-wrap gap-2">
          {activeFollowups.map((prompt) => (
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
      ) : null}

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

function MessageBubble({ message, lang }: { message: ChatMessage; lang: Lang }) {
  if (message.role === "tool") return <ToolCallChip message={message} />;

  const isUser = message.role === "user";
  // Prefer the tri-lingual bundle authored at write time (by the
  // orchestrator for assistant turns, and for user turns via the same
  // verbatim-translation pass). Falls back to the canonical single-
  // locale `content` if the bundle is absent or the requested locale
  // was not stored.
  const displayed = message.content_i18n?.[lang] ?? message.content;
  return (
    <div
      className={cn(
        "flex max-w-[85%] flex-col gap-2 rounded-2xl border px-4 py-3 text-sm leading-relaxed",
        isUser
          ? "ml-auto rounded-br-sm border-primary bg-primary text-primary-foreground"
          : "mr-auto rounded-bl-sm border-border bg-card text-card-foreground"
      )}
    >
      <div className="whitespace-pre-wrap">{displayed}</div>
      {message.chart_spec ? (
        <div className="rounded-lg border border-border/70 bg-background p-2 text-foreground">
          <ChartRenderer spec={message.chart_spec} />
        </div>
      ) : null}
    </div>
  );
}

/** Compact chip rendered when the orchestrator calls a deterministic tool.
 *  Makes Qwen's native tool-calling loop visible to the audience instead of
 *  burying it inside a normal-looking assistant bubble. */
function ToolCallChip({ message }: { message: ChatMessage }) {
  const { t } = useT();
  const label = message.content
    ? t("chat_tool_running", { name: message.content })
    : t("chat_tool_generic");
  return (
    <div className="mr-auto flex items-center gap-2 rounded-full border border-primary/30 bg-primary/5 px-3 py-1.5 text-xs text-primary">
      <Wrench className="size-3.5" />
      <span className="font-medium">{label}</span>
    </div>
  );
}
