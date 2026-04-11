# Scale-Up Path

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

---

## 17. Scale-Up Path

The PoC runs on a single 12GB GPU. The solution architecture is identical at scale — only the compute layer changes.

### Compute Scale-Up Options

| Stage | Model | Hardware | Concurrent Users | Monthly Cost |
|---|---|---|---|---|
| **PoC** | Qwen3-8B Q4_K_M | 1x RTX 3060 12GB | 1-2 | ~$0 (local) |
| **Pilot (100 users)** | Qwen3-14B FP8 | 1x A100 80GB | 10-20 | ~$1,500-2,000 |
| **Production (1,000 users)** | Qwen3-14B FP8 | 4x A100 80GB | 50-80 | ~$6,000-9,000 |
| **Scale (10,000+ users)** | Qwen3-32B FP8 | 2x H100 80GB + horizontal | 200+ | ~$12,000-24,000 |

### Inference Backend Scale-Up

| Stage | Backend | Why |
|---|---|---|
| PoC | llama.cpp / Ollama | Simplest, single-user, no config overhead |
| Pilot | vLLM | Paged attention, better batching |
| Production | SGLang | 29% throughput advantage over vLLM; 6x better for shared system prompts (our use case) |

### Database Scale-Up

| Stage | Database | Why |
|---|---|---|
| PoC | SQLite | Zero-infra, single-file |
| Pilot | PostgreSQL | Multi-user, ACID, concurrent access |
| Production | PostgreSQL + Qdrant (distributed) | PostgreSQL for relational data; Qdrant cluster for vector search at scale |

### Model Quality Scale-Up

| Stage | Approach |
|---|---|
| PoC | Qwen3-8B Q4 — general-purpose, zero fine-tuning |
| Pilot | Qwen3-14B FP8 — higher quality, still general-purpose |
| Production | Fine-tuned Qwen3-14B on Vietnamese banking terminology + customer interaction data |
| Advanced | Specialist fine-tuned models per agent (spending analyst, product recommender) similar to TojiMoola's specialist sub-models |

### Vietnam-Specific Cloud GPU Options

| Provider | GPUs Available | Notes |
|---|---|---|
| **GreenNode / VNG Cloud** | H100, A40, L40S, RTX 5090 | Two AI data centres (STT VNG HCMC 1 & 2) operational H1 2026 |
| **FPT AI Factory** | Thousands of H100 (HGX B300) | Operational since January 2025, GPU Cloud for inference/training |
| **CMC Cloud** | General compute | Lags on GPU-specific offerings |
| **AWS/GCP Singapore** | Full GPU range | Higher latency, data localisation concerns |

Vietnam's Cybersecurity Law imposes data localisation requirements on certain financial data, making local providers strategically important for Shinhan.

**On-premise costs:** Single H100 80GB SXM: USD 30,000-40,000. 8-GPU server: USD 200,000-400,000 fully loaded. Lead times: 5-6 months. 3-5 year hardware refresh cycles.

### SGLang Prefix Caching for Tool-Calling Agents

SGLang's RadixAttention stores KV activations in a radix tree keyed on exact byte sequences. For agentic workloads with shared system prompts and tool schemas, cache hit rates reach **75-95%**, with TTFT of ~41ms at 2,620 tok/s. Critical constraint: system prompt and tool schema must be pinned as byte-identical constants — any whitespace drift creates a full cache miss. Reports **4-6x throughput over baseline vLLM** on agentic tasks.

### Fine-Tuning Economics

| Method | Min Dataset | Hardware | Cost | Quality Recovery |
|---|---|---|---|---|
| LoRA (r=16, alpha=16) | 1,000-5,000 examples | 1x A100 | ~$30-100 | 90-95% of full FT |
| QLoRA | 1,000-5,000 examples | 1x RTX 4090 | ~$10-30 | 80-90% of full FT |
| Full fine-tuning | 5,000-10,000 examples | Multiple H100s | ~$1,000+ | 100% (baseline) |

### Bank-Grade SLA (99.9%) Serving Pattern

Kubernetes-managed SGLang pods behind application-layer load balancer, with weighted routing away from degraded instances. Separate inference pools: interactive chat (latency-sensitive, small batch) and background agents (throughput-optimised, large batch) to prevent head-of-line blocking. Blue-green deployments for model upgrades without downtime.

---
