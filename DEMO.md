# Lodestar — Live demo walkthrough

A judge-ready 3-minute narrative against the live deployment.

**Live URLs**

- Frontend: <http://43.98.179.20:3000/?demo=1>
- Backend API: <http://43.98.179.20:8000>

The `?demo=1` query flag reveals the floating **Simulate** button used for
the preset transactions below. Without the flag, the app only reacts to
real SOL-side transactions — matching the production embedding mode.

---

## Before you start

- Open the frontend URL in a wide browser window. The app is responsive,
  but the four-subsidiary scenario grid reads best at ≥ 1200px.
- Click the **Simulate** button (bottom-right) once, then click the
  **Reset demo** button at the top of the drawer. Close the drawer.
  You now have an empty feed, an empty memory, and no lessons.
- Confirm the language is Vietnamese using the globe icon in the header.
  Greeting should read *"Xin chào"*.

Total time: ~3 minutes if narrated fluently; detector emissions add the
only variable latency (typically 20–40 s per life-event card).

---

## Stage 1 — Zero-latency tri-lingual toggle (15 seconds)

Click the globe icon in the header. Pick **Tiếng Anh**. The greeting
flips to *"Hello"*, the nav reads *"Feed · Plan · Products"*, the footer
reads *"Powered by Qwen"*. Click the globe again, pick **한국어**.
Greeting *"안녕하세요"*, nav *"피드 · 계획 · 상품"*. Pick **Tiếng Việt**
to return.

> "Every string the customer sees — nav chrome, card titles, chat
> bubbles, chart captions, follow-up chips — is authored in all three
> locales at write time by a single structured-output LLM call. The
> toggle isn't a translation step; it's a render step. Zero
> round-trips."

---

## Stage 2 — The agent synthesising signals (45 seconds)

Open the **Simulate** drawer again. Under **Sự kiện — em bé** (baby
preset group), click the three presets in order:

1. **Kids Plaza 2.1M** — signals new-baby purchasing start
2. **Con Cưng 1.8M** — reinforces (second baby-related merchant)
3. **Bệnh viện Phụ sản 3.5M** — hospital signal, crosses a higher spend
   threshold

Close the drawer. Scroll to the feed's empty state — *"Chưa có insight
nào. Coach đang theo dõi giao dịch của bạn…"* Wait ~30 s. A card streams
in via SSE:

> **Sự kiện cuộc sống — Dấu hiệu chuẩn bị đón em bé**  
> *"Giao dịch 2,1 triệu VND tại Kids Plaza kết hợp với 5 giao dịch gần
> đây cho thấy dấu hiệu chuẩn bị đón em bé."*
> *"Đây là thông tin tham khảo, không phải tư vấn tài chính."*

> "Ten rule-based sensors are available to the LLM as callable tools.
> It chose life-event pattern, large outflow, and first-time merchant,
> decided they told one story, and composed this card. Silent on noise,
> synthesised on signal — the judgement call competitors' threshold
> alerts cannot make. Notice the compliance disclaimer auto-appended
> — the classifier ran before the card was written to the feed."

---

## Stage 3 — Drill-down chat, tri-lingual user bubble (45 seconds)

Click the card. Ask, **in Korean**:

```
출산 전에 얼마를 저축하면 좋을까요?
```

Watch the Wrench-chip appear briefly (*"Đang gọi công cụ
scenario_simulation…"*) while the orchestrator invokes its tool loop.
Reply arrives with a compliance refusal — the coach correctly declines
to quote a specific savings amount, which is personalised advice.

Click the globe. Switch to **English**. The user bubble becomes *"How
much should I save before giving birth?"* The assistant reply is in
English. Switch to **Korean**. User bubble *"출산 전에 얼마를 저축하면
좋을까요?"*. Switch back to **Vietnamese**. User bubble *"Liệu tôi nên
tiết kiệm bao nhiêu trước khi sinh con?"*.

> "The user typed in Korean while the UI was in Vietnamese. The
> orchestrator's final JSON turn authored the user's message in all
> three locales — not just the assistant's reply. Every toggle here is
> a pure render. And compliance ran in all three locales at the same
> severity — a Vi refusal would never ship next to untreated En advice."

Click **Quay lại bảng tin** (back to feed), then click the card again.
The conversation is fully restored — tool chip, user bubble, assistant
bubble, all three locales intact. That's the `/chat/{id}/history`
endpoint replaying from the interaction ledger.

---

## Stage 4 — The agent learns (30 seconds)

Dismiss the card by clicking the X on the top-right. A toast confirms.
Open **Simulate** again and scroll to the **Bộ nhớ của Coach** section.
You see:

- **Bài học (2)** — two lessons, one from the chat engagement
  (*earned reward*, 95% confidence) and one from the dismissal
  (*reduce frequency*, 85% confidence)
- **Phản hồi (2)** — two reflections quadrant-coded: one *earned_reward*,
  one *bad_luck*
- **Cohort (hà_nội_mass)** — the customer's non-PII cohort key, ready
  to aggregate cross-customer patterns once 5+ customers share the
  same trigger

> "This is the piece the brief didn't ask for. Every dismissal, every
> chat, every goal creation teaches the coach. Van Tharp quadrants
> separate process quality from outcome quality — you don't learn
> bad process from a good outcome. Over time, the lessons compound.
> A fresh-install competitor can't match that."

---

## Stage 5 — Cross-entity scenario simulator (30 seconds)

Tap the **Kế hoạch** (Plan) nav button. Scroll down to **Mô phỏng kịch
bản**. Use the arrow keys to cycle through the four scenarios — *Mua
nhà*, *Đổi việc*, *Có em bé*, *Kết hôn*. Land on **Kết hôn**. Confirm the
defaults (partner income 12M, wedding cost 200M). Click **Chạy mô
phỏng**.

The result renders in one shot:

- **Kết quả tổng hợp:** *"Dòng tiền hàng tháng: 11,597,856 → 23,597,856
  VND"* — dual income almost doubles monthly cashflow.
- Four entity-impact cards below:
  - **Ngân hàng** — combined income, current savings
  - **Tài chính tiêu dùng** — wedding + home setup cost 200M VND
  - **Bảo hiểm nhân thọ** — coverage gap: current 12M → recommended 1.4B

Toggle the language. Every number stays. Every label translates.

> "A single click computes the impact across all four Shinhan
> subsidiaries. A bank-only competitor can show you the mortgage side.
> Shinhan's four-subsidiary footprint lets Lodestar show the whole
> impact — and cross-sell the product that closes the gap."

---

## Stage 6 — Product search in any language (15 seconds)

Tap the **Sản phẩm** (Products) nav button. Type, in Korean:

```
신용카드
```

Five Shinhan products return — credit cards from Bank, Consumer Finance,
plus an auto loan — ranked by eligibility. Each card shows the
interest-rate chip, minimum-income chip, and the subsidiary tag.

Toggle the language. Product names flip between Vietnamese, English, and
Korean using the server-side i18n projection.

> "`bge-m3` is a multilingual embedding model. The Shinhan catalogue is
> indexed once, in Vietnamese, and retrieves correctly from any of the
> three input languages. The eligibility filter is customer-specific —
> only the products this customer qualifies for appear here."

---

## Close

> "Lodestar watches, reasons, composes in three languages at once,
> routes into Shinhan's own catalogue, and learns from every
> interaction. It's not a chatbot — it's an autonomous agent that
> compounds. The memory layer is the moat. The four-subsidiary
> simulator is the proof. And every feature on the screen maps
> directly to one of the five KPIs the SB1 brief asked us to move."

---

## Reset between runs

From any screen, open **Simulate** → **Đặt lại bản demo**. Clears the
insight feed, demo transactions, goals, lessons, and reflections for
customer C001. The baseline transaction history stays — resetting only
the demo overlay, not the synthetic customer state.
