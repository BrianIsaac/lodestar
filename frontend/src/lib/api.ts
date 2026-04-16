/** FastAPI client for the financial coach backend. */

import type {
  ChatResponse,
  InsightCard,
  InsightFeed,
  ProductInfo,
  SavingsGoal,
  ScenarioResult,
} from "./types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchFeed(
  customerId: string,
  language: string = "vi"
): Promise<InsightFeed> {
  const params = new URLSearchParams({ language });
  const res = await fetch(`${API}/feed/${customerId}?${params.toString()}`);
  if (!res.ok) throw new Error(`Feed error: ${res.status}`);
  return res.json();
}

export async function dismissInsight(
  insightId: string,
  customerId: string
): Promise<void> {
  await fetch(`${API}/dismiss/${insightId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customer_id: customerId }),
  });
}

export async function sendChat(
  insightId: string | null,
  customerId: string,
  message: string,
  insightContext?: string,
  language: string = "vi"
): Promise<ChatResponse> {
  const endpoint = insightId ? `${API}/chat/${insightId}` : `${API}/chat`;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      customer_id: customerId,
      message,
      insight_context: insightContext ?? "",
      language,
    }),
  });
  if (!res.ok) throw new Error(`Chat error: ${res.status}`);
  return res.json();
}

export async function simulateScenario(
  customerId: string,
  scenarioType: string,
  parameters: Record<string, unknown>,
  language: string = "vi"
): Promise<ScenarioResult> {
  const res = await fetch(`${API}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      customer_id: customerId,
      scenario_type: scenarioType,
      parameters,
      language,
    }),
  });
  if (!res.ok) throw new Error(`Simulation error: ${res.status}`);
  return res.json();
}

export async function fetchGoals(customerId: string): Promise<SavingsGoal[]> {
  const res = await fetch(`${API}/goals/${customerId}`);
  if (!res.ok) throw new Error(`Goals error: ${res.status}`);
  return res.json();
}

export async function createGoal(
  customerId: string,
  name: string,
  targetAmount: number,
  targetDate: string
): Promise<SavingsGoal> {
  const res = await fetch(`${API}/goals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      customer_id: customerId,
      name,
      target_amount: targetAmount,
      target_date: targetDate,
    }),
  });
  if (!res.ok) throw new Error(`Create goal error: ${res.status}`);
  return res.json();
}

export async function searchProducts(
  query: string,
  language: string = "vi"
): Promise<ProductInfo[]> {
  const params = new URLSearchParams({ query, language });
  const res = await fetch(`${API}/products/search?${params.toString()}`);
  if (!res.ok) throw new Error(`Search error: ${res.status}`);
  return res.json();
}

export interface RecentTransaction {
  transaction_id: string;
  date: string;
  amount: number;
  category: string;
  merchant: string;
  entity: string;
}

export async function fetchRecentTransactions(
  customerId: string,
  limit: number = 8
): Promise<RecentTransaction[]> {
  const res = await fetch(`${API}/transactions/${customerId}?limit=${limit}`);
  if (!res.ok) throw new Error(`Transactions error: ${res.status}`);
  return res.json();
}

export interface DemoTransactionPayload {
  customer_id: string;
  merchant: string;
  amount: number;
  category?: string;
  entity?: string;
  description?: string;
}

export interface DemoTransactionResult {
  transaction_id: string;
  transaction: {
    merchant: string;
    amount: number;
    category: string;
    entity: string;
    date: string;
  };
  agent_pending: boolean;
  /** Kept for compat with earlier versions — no longer populated now
   *  that the detector agent runs asynchronously. */
  new_insights?: InsightCard[];
}

export async function postDemoTransaction(
  payload: DemoTransactionPayload
): Promise<DemoTransactionResult> {
  const res = await fetch(`${API}/demo/transaction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Demo injection error: ${res.status}`);
  return res.json();
}

export interface DemoResetResult {
  customer_id: string;
  cards_deleted: number;
  demo_transactions_deleted: number;
}

export async function postDemoReset(customerId: string): Promise<DemoResetResult> {
  const res = await fetch(`${API}/demo/reset/${customerId}`, { method: "POST" });
  if (!res.ok) throw new Error(`Demo reset error: ${res.status}`);
  return res.json();
}
