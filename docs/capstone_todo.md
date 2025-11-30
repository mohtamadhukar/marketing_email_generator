
We are building a **Personalized Email Generator for Marketers** for a grocery retail chain (e.g., **HEB**). It’s a lightweight, multi-agent system that takes a structured **campaign brief** from marketers, generates on-brand and compliant email variants (A/B), and outputs an ESP-ready JSON payload. The demo will show agents collaborating, applying brand rules, ensuring safety, and exporting a structured campaign output — all deployed on minimal Google Cloud infrastructure (Cloud Run + Vertex AI + ADK).

The marketer provides a **Campaign Brief JSON** as input. Agents use that structured brief to generate and validate the campaign outputs.

---

## 🧩 Campaign Brief JSON Schema

This JSON defines what marketers submit to start a campaign. Example below is for a grocery chain like HEB.

```json
{
  "brand": "HEB",
  "campaign": {
    "name": "Holiday Fresh Savings",
    "goal": "Re-engage lapsed shoppers before the holiday season",
    "objective": "Increase online grocery orders by 15% in November",
    "start_date": "2025-11-20",
    "end_date": "2025-12-15"
  },
  "audience": {
    "segment": "lapsed_customers_30d",
    "persona": "Budget-conscious family shopper",
    "locale": "en-US",
    "preferred_store": "San Antonio #104",
    "preferences": ["fresh produce", "weekly deals", "curbside pickup"]
  },
  "offer": {
    "type": "Discount",
    "headline": "Fresh Savings, Just for You!",
    "details": "15% off on fresh produce and dairy products",
    "coupon_code": "HOLIDAY15",
    "valid_till": "2025-12-15"
  },
  "creative_guidelines": {
    "tone": "Friendly, community-focused, and helpful",
    "banned_phrases": ["limited stock", "exclusive access"],
    "disclaimer": "Offers valid while supplies last. Prices may vary by store.",
    "cta_examples": ["Shop Now", "Order Online", "Grab Your Discount"]
  },
  "channel": {
    "type": "Email",
    "target_platform": "Mailchimp",
    "ab_variants": true
  },
  "success_metrics": {
    "kpi": ["open_rate", "click_rate", "conversion_rate"],
    "target_values": {"open_rate": 0.3, "click_rate": 0.1}
  }
}
```

This becomes the input payload for your orchestrator.

---

## ✅ Stage 0: Project Setup and Environment

**Goal:** Set up development environment, repo, and cloud basics.

### Tasks
- [x] Create a new Git repo with structure:
  - `/agents/` (for ADK agent code)
  - `/tools/` (for MCP + OpenAPI tools)
  - `/data/` (for synthetic data + brand rules)
  - `/schemas/` (for ESP payload schema)
  - `/demo/` (for frontend or CLI)
- [x] Configure local `.env` with dev variables.

**Acceptance Criteria:** Local environment ready; Cloud Run + Vertex AI credentials verified.

---

## ✅ Stage 1: Data Creation and Brand Rules

**Goal:** Prepare the synthetic inputs required for demo.

### Tasks
- [x] Create `profiles.json` — 10–50 mock customers with fields:
  - name, segment, gender, locale, last_action, preferences
- [x] Create `events.json` — recent behaviors like *viewed product*, *added to cart*, *inactive 30 days*.
- [x] Create `brand_rules.json` — tone, banned phrases, CTA rules, length limits, disclaimers.
- [x] Create `baseline_email_template.json` — safe default email template.

**Acceptance Criteria:** All data files load successfully; brand and templates defined.

---

## ✅ Stage 2: ADK Agent Skeleton

**Goal:** Set up the orchestrator and core agent flow.

### Tasks
- [ ] Initialize ADK project.
- [ ] Implement agents:
  1. `OrchestratorAgent` — controls flow, aggregates outputs.
  2. `ProfileAgent` — retrieves + compacts data.
  3. `CopyAgent` — generates subject + body variants (parallel calls).
  4. `BrandAgent` — enforces tone/style rules.
  5. `SafetyAgent` — checks compliance and spam.
  6. `PackagingAgent` — outputs structured ESP JSON.
- [ ] Define data contracts between agents using A2A protocol.
- [ ] Implement one sequential demo flow (happy path).

**Acceptance Criteria:** Local run completes full generation with sample input.

---

## ✅ Stage 3: Tools (MCP + Built-in + OpenAPI)

**Goal:** Add interoperability and mock integrations.

### Tasks
- [ ] MCP Servers:
  - `customer_data` — get_profile, get_recent_events.
  - `brand_assets` — load brand book JSON.
  - `esp_connector` — mock send_to_esp tool returning confirmation.
- [ ] Built-in tools:
  - Code tool: spam keyword checks, ALL-CAPS limit, length validation.
- [ ] OpenAPI tool:
  - Mock `POST /createDraft` for one ESP.
- [ ] Implement structured error handling and fallback.

**Acceptance Criteria:** Tools callable individually; agent orchestrator integrates with MCP successfully.

---

## ✅ Stage 4: Context, Session, and Memory

**Goal:** Add short-term and long-term state management.

### Tasks
- [ ] Add ADK **InMemorySessionService** for per-request state.
- [ ] Implement **context compaction** (limit tokens, summarize history, truncate past steps).
- [ ] (Optional) Simulate **Memory Bank** — store best-performing email variants for reuse.

**Acceptance Criteria:** Context trimming visible in logs; memory store writes asynchronously.

---

## ✅ Stage 5: Guardrails and Loop Logic

**Goal:** Enforce safety and retry logic.

### Tasks
- [ ] Implement brand/style enforcement logic in `BrandAgent`.
- [ ] Add `SafetyAgent` rules:
  - detect PII, spam terms, length > limit, or banned tone.
- [ ] Orchestrator triggers one re-generation loop if SafetyAgent fails.
- [ ] Fallback: revert to baseline email template after one failed loop.

**Acceptance Criteria:** Controlled re-generation; fallback works on failed outputs.

---

## ✅ Stage 6: Pause and Resume (Long-Running)

**Goal:** Support manual review checkpoint.

### Tasks
- [ ] Store workflow state (stage, cursor) in memory or Firestore.
- [ ] Implement `/pause` and `/resume` endpoints in orchestrator.
- [ ] Demo: Pause after SafetyAgent → manual approval → resume PackagingAgent.

**Acceptance Criteria:** Demo shows successful pause/resume flow with state retained.

---

## ✅ Stage 7: Observability and Metrics

**Goal:** Instrument logging, tracing, and metrics.

### Tasks
- [ ] Structured logging per agent (run_id, tokens, latency, pass/fail).
- [ ] Distributed tracing spans via ADK (OpenTelemetry → Cloud Trace).
- [ ] Expose /metrics endpoint or print summary metrics:
  - latency (p50, p95)
  - safety pass rate
  - governance score
  - token usage
- [ ] Optional: visualize traces in Cloud console.

**Acceptance Criteria:** One trace visible in Cloud Trace; logs include latency and scores.

---

## ✅ Stage 8: Evaluation Harness

**Goal:** Show measurable output quality.

### Tasks
- [ ] Build gold dataset (20 scenarios with baseline outputs).
- [ ] Automated checks:
  - JSON schema validity
  - brand/safety pass
  - subject length < 60 chars
- [ ] Implement LLM-as-a-Judge evaluator (pairwise scoring vs baseline).
- [ ] Save evaluation metrics to `/eval/results.json`.

**Acceptance Criteria:** Evaluation run prints summary table with pass/win rates.

---

## ✅ Stage 9: Demo UI or CLI

**Goal:** Create user interface for live demonstration.

### Tasks
- [ ] Streamlit UI or simple CLI with inputs:
  - customer_profile.json
  - campaign_goal (text)
  - generate button
- [ ] Display progress logs (agent stages, pause/resume events).
- [ ] Show final ESP JSON output + metrics summary.
- [ ] Include demo toggle: “Trigger Safety Violation” to show loop/pause.

**Acceptance Criteria:** End-to-end demo visible; JSON downloadable.

---

## ✅ Stage 10: Deployment and Dry Run

**Goal:** Deploy working demo to Google Cloud.

### Tasks
- [ ] Containerize app; push to Artifact Registry.
- [ ] Deploy to Cloud Run with env vars + Secret Manager integration.
- [ ] Run dry-run demo in console and Cloud Run logs.
- [ ] Record final demo (screen capture or live run).

**Acceptance Criteria:** Cloud Run URL live; demo executes successfully; logs visible.

---

## ✅ Stage 11: Presentation Prep

**Goal:** Package the demo for reviewers.

### Tasks
- [ ] Screenshot architecture diagram (agents, tools, Google Cloud services).
- [ ] Export sample Cloud Trace span screenshot.
- [ ] Include evaluation summary table.
- [ ] Write README.md with:
  - How to run locally and on Cloud Run
  - Agent roles + flow diagram
  - Rubric mapping table (multi-agent, tools, memory, safety, evaluation)
  - Known limitations

**Acceptance Criteria:** Reviewers can reproduce the demo with one command.

---

## Suggested Build Order
1. Setup & data (Stages 0–1)
2. ADK skeleton + tools (Stages 2–3)
3. Context + safety (Stages 4–5)
4. Pause/resume + observability (Stages 6–7)
5. Evaluation + UI (Stages 8–9)
6. Deploy + document (Stages 10–11)

---

**Final Deliverable:**
A live demo (Cloud Run + Vertex AI) showing:
- Multi-agent orchestration (parallel + sequential)
- Context compaction and memory
- Pause/resume workflow
- Observability traces + metrics
- Safe, ESP-ready email JSON output

