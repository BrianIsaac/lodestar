/** FastAPI client for the financial coach backend. */

import type {
  ChatResponse,
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
  parameters: Record<string, unknown>
): Promise<ScenarioResult> {
  const res = await fetch(`${API}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      customer_id: customerId,
      scenario_type: scenarioType,
      parameters,
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

export async function searchProducts(query: string): Promise<ProductInfo[]> {
  const res = await fetch(
    `${API}/products/search?query=${encodeURIComponent(query)}`
  );
  if (!res.ok) throw new Error(`Search error: ${res.status}`);
  return res.json();
}
