/** Shared TypeScript types matching the FastAPI Pydantic models. */

export interface ChartSpec {
  chart_type: string;
  title: string;
  data: Record<string, unknown>;
  axes?: Record<string, string> | null;
  summary: string;
}

export interface InsightCard {
  insight_id: string;
  customer_id: string;
  title: string;
  summary: string;
  severity: "life_event" | "anomaly" | "milestone" | "info" | "product";
  chart_spec?: ChartSpec | null;
  suggested_actions: string[];
  compliance_class: "information" | "guidance" | "advice";
  priority_score: number;
  dismissed: boolean;
}

export interface InsightFeed {
  customer_id: string;
  cards: InsightCard[];
  total: number;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  chart_spec?: ChartSpec | null;
}

export interface ChatResponse {
  message: ChatMessage;
  suggested_followups: string[];
}

export interface SavingsGoal {
  goal_id: string;
  customer_id: string;
  name: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
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

export interface ProductInfo {
  product_id: string;
  entity: string;
  product_type: string;
  name_vi: string;
  name_en: string;
  description_vi: string;
  interest_rate: number | null;
  min_income: number | null;
}
