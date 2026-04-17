/** Shared TypeScript types matching the FastAPI Pydantic models. */

export interface ChartSpec {
  chart_type: string;
  title: string;
  data: Record<string, unknown>;
  axes?: Record<string, string> | null;
  summary: string;
}

export interface QuickPrompt {
  text: string;
  action: "chat" | "plan" | "products" | string;
  params?: Record<string, unknown>;
}

export interface InsightCard {
  insight_id: string;
  customer_id: string;
  title: string;
  summary: string;
  title_i18n?: Record<string, string> | null;
  summary_i18n?: Record<string, string> | null;
  action_hint_i18n?: Record<string, string[]> | null;
  quick_prompts_i18n?: Record<string, QuickPrompt[]> | null;
  severity: "life_event" | "anomaly" | "milestone" | "info" | "product";
  chart_spec?: ChartSpec | null;
  suggested_actions: string[];
  compliance_class: "information" | "guidance" | "advice";
  priority_score: number;
  dismissed: boolean;
  created_at?: string;
}

export interface InsightFeed {
  customer_id: string;
  cards: InsightCard[];
  total: number;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  content_i18n?: Record<string, string> | null;
  chart_spec?: ChartSpec | null;
}

export interface ChatResponse {
  message: ChatMessage;
  suggested_followups: string[];
  suggested_followups_i18n?: Record<string, string[]> | null;
  tool_calls?: string[];
}

export interface SavingsGoal {
  goal_id: string;
  customer_id: string;
  name: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
  created_at: string;
}

export interface EntityImpact {
  entity: string;
  summary: string;
  metrics: Record<string, number>;
}

export interface ScenarioResult {
  customer_id: string;
  scenario_type: string;
  entity_impacts: EntityImpact[];
  combined_summary: string;
  monthly_cashflow_before: number;
  monthly_cashflow_after: number;
  risk_flags: string[];
}

export type Language = "vi" | "en" | "ko";

export interface ProductInfo {
  product_id: string;
  entity: string;
  product_type: string;
  name_vi: string;
  name_en: string;
  name_ko: string;
  description_vi: string;
  description_en: string;
  description_ko: string;
  /** Display name resolved to the requested language by the API. */
  name: string;
  /** Display description resolved to the requested language by the API. */
  description: string;
  interest_rate: number | null;
  min_income: number | null;
}
