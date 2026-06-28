# AI Architect & Practitioner Bootcamp — Study Guide

**Purpose:** Key learnings, architecture principles, production lessons, and decision frameworks from all 26 chapters.  
**Audience:** Practitioners preparing for AI architect roles, certification exams, or senior technical interviews.  
**How to use:** Read chapter summaries for orientation. Use Quick Reference tables before interviews. Use Production Lessons to ground architecture decisions in real outcomes.

---

## The Book's Central Thesis

> Artificial Intelligence is not about building the smartest model. It is about solving the right business problem with the simplest architecture that delivers measurable value.

## The Five-Lens Framework

Every AI architecture decision should be evaluated through five lenses:

| Lens | Question |
|---|---|
| **Science** | How does it work? What are the limitations? |
| **Engineering** | How do you build it reliably and testably? |
| **Architecture** | How does it fit into the enterprise system? |
| **Business Value** | What ROI does it create? At what cost? |
| **Leadership** | Who owns it? How is it governed? |

---

## Chapter 00 — Preface

**The Four Pillars of Every AI System:**
1. Business Value — measurable outcome, not model performance
2. Technical Soundness — architecture patterns, not prompts
3. Operational Readiness — evaluation, observability, governance
4. Human Accountability — people remain responsible for consequential decisions

**The Capstone Thread:** All chapters build toward the Enterprise Agentic Operations Platform — a governed platform for device incident investigation, support drafting, and executive communication.

---

## Chapter 01 — Evolution of AI

**AI Capability Generations:**
- Rule-Based → Statistical ML → Deep Learning → Foundation Models → Agentic AI

**The AI Value Chain:** Problem → Data → Model → Platform → Workflow → User → Outcome → ROI

**When NOT to use AI:**
- Deterministic rules solve it completely
- Data is insufficient or ungoverned
- Accountability cannot be assigned
- Cost exceeds value
- Speed requirement eliminates verification

**Key Regulatory Frameworks:**

| Framework | Scope | Key Requirement |
|---|---|---|
| EU AI Act | All AI in EU/EU-adjacent | Risk tiers; conformity assessment for high-risk |
| NIST AI RMF | US (voluntary) | Govern → Map → Measure → Manage |
| ISO/IEC 42001 | International | AI management system standard |

**AI Operating Models:**
- **COE (Center of Excellence):** Centralized standards, shared platform, governance — risk: bottleneck
- **Embedded Teams:** Fast, domain-close — risk: fragmented governance
- **Federated Hybrid:** COE owns platform and standards; product teams own workflows ← most mature enterprises converge here

**Production Lesson:** AI amplifies data, workflows, decisions, teams, and operating models — both their strengths and their weaknesses.

---

## Chapter 02 — Large Language Models

**Token Economics:**
- Everything is tokens: input, output, cached, batch
- Output tokens are typically 3–5× more expensive than input tokens
- Cost = (input_tokens × input_rate) + (output_tokens × output_rate)

**Key LLM Concepts:**

| Concept | What It Means for Architecture |
|---|---|
| Temperature | 0.0 for factual/grounding tasks; 0.7+ for generation/creativity |
| Context window | Hard limit on input; longer context ≠ better reasoning |
| Hallucination | Model generates plausible-sounding incorrect text; requires grounding |
| Tokenization | Unexpected splits affect prompts; use token counter before API calls |
| Embeddings | Dense vector representations; foundation of semantic search and RAG |

**Fine-Tuning Decision:**

```
Prompt engineering → RAG → LoRA/QLoRA → Full fine-tuning
(cheapest) ──────────────────────────────── (most expensive)
```

- **LoRA:** Adds small low-rank adapter matrices; trains ~1–5% of parameters; base model frozen
- **QLoRA:** LoRA + 4-bit quantized base model; enables fine-tuning of large models on modest GPU
- **When to fine-tune:** Style consistency, repeated structured extraction, cost at scale — NOT for adding current knowledge (use RAG)

**Model Family Reference:**

| Category | Examples | Enterprise Strength |
|---|---|---|
| Frontier API | Claude, GPT-4o, Gemini | Strong general capability, managed |
| Open-weight | Llama, Mistral, Phi, Qwen | Data sovereignty, fine-tuning control |
| Embedding | text-embedding-3, Cohere embed | RAG, semantic search |
| Multimodal | Claude Vision, GPT-4o vision | Document parsing, image analysis |

**Multimodal Architecture Patterns:**
1. Single multimodal model (image + text → model → text)
2. Specialized pipeline (image → vision model → text → LLM)
3. Multimodal RAG (parse visual documents → index → retrieve)

**Principle:** The benchmark model is rarely the production model. Evaluate on your tasks.

---

## Chapter 03 — Prompt Engineering and Context Design

**The Prompt Hierarchy:**
1. System prompt — platform-level persistent instructions
2. Developer prompt — application-level context and rules
3. User prompt — per-request input

**PromptOps Maturity Levels:**
1. Ad hoc (prompts in code)
2. Templated (variables substituted)
3. Versioned (registry, owner, approval)
4. Evaluated (golden dataset against each version)
5. Managed (CI/CD gate, cost regression, automated rollback)

**Prompt Injection — The Two Types:**
- **Direct injection:** User explicitly attempts to override instructions in their message
- **Indirect injection:** Malicious instructions embedded in retrieved documents or tool results

**Critical Rule:** Prompts are not security boundaries. Authorization belongs in code, not instructions.

**Production Template Structure:**
```
SYSTEM: [Stable instructions — cache this]
TASK: [What the model should do]
CONTEXT: [Retrieved evidence — permission-filtered]
USER INPUT: [User's actual request — validated]
OUTPUT FORMAT: [Schema or structure requirement]
```

**Cost Optimization in Prompts:**
- Cache stable system prompts (saves 60–90% on repeated calls)
- Compress retrieved context to fit token budget
- Remove few-shot examples when fine-tuning achieves the same behavior
- Track token count per prompt version — bloat is invisible without dashboards

**Principle:** Prompt engineering is interface design for probabilistic systems.

---

## Chapter 04 — Retrieval-Augmented Generation (RAG)

**The RAG Pipeline:**
```
Query → Embed → Search (Vector + Lexical) → Rerank → Assemble Context → Generate → Cite
```

**RAG vs Alternatives:**

| Approach | Use When |
|---|---|
| RAG | Knowledge changes frequently; large corpus; citations needed |
| Fine-tuning | Style/format consistency; repeated task pattern; stable domain vocabulary |
| Long context | Small corpus; deep cross-document reasoning; infrequent queries |
| Tools | Live/real-time data; calculations; authoritative system of record |

**Permission-Aware Retrieval:**
- Filter at the vector store query level — NOT after retrieval, NOT by the model
- Every document must carry `tenant_id` and classification metadata
- Cross-tenant isolation test must be in every golden dataset

**RAG Failure Modes:**

| Failure | Symptom | Root Cause |
|---|---|---|
| Missing evidence | Model says "I don't know" | Retrieval returned nothing useful |
| Stale evidence | Incorrect but dated answer | Source not refreshed |
| Wrong evidence | Plausible but wrong | Retrieval quality low |
| Hallucinated citation | Confident, untrue | Model fabricated reference |
| Permission leak | Tenant B sees Tenant A data | Filter not applied |

**Advanced RAG Patterns:**
- **Graph RAG:** When entity relationships matter (device→firmware→error→runbook)
- **Agentic RAG:** Agent decides which sources to query and in what order
- **Multimodal RAG:** Parse visual documents (tables, charts, images) before indexing

**Principle:** Retrieval quality is AI quality. A perfect model on wrong evidence produces wrong answers.

---

## Chapter 05 — Vector Databases and Retrieval Systems

**Core Indexing Algorithms:**

| Algorithm | Best For | Tradeoff |
|---|---|---|
| HNSW | Low-latency approximate search | Higher memory |
| IVF | Large-scale approximate search | Recall vs speed tunable |
| Flat/exact | Small corpora, highest recall | Scales poorly |

**Similarity Metrics:**
- **Cosine similarity:** Angle between vectors; model-independent magnitude; most common for NLP
- **Dot product:** Cosine × magnitude; use when magnitude carries meaning
- **L2/Euclidean:** Absolute distance; use for embeddings trained with L2 objective

**Hybrid Search:** Combine vector similarity (semantic) with BM25 (keyword/exact). Critical for queries containing product codes, error codes, firmware versions, or identifiers that semantic search misses.

**Build vs Buy Decision:**

| Option | Use When |
|---|---|
| pgvector (PostgreSQL extension) | Already on PostgreSQL; <10M vectors; hybrid SQL+vector |
| Managed cloud (Pinecone, OpenSearch Serverless) | Fast start; standard RAG; minimize ops |
| Self-hosted (Weaviate, Qdrant, Milvus) | Data sovereignty; custom ranking; cost at scale |
| In-process (FAISS, Chroma) | Prototyping and offline only |

**pgvector Key Facts:**
- Supports HNSW index (since v0.5)
- `vector_cosine_ops` for cosine distance
- JSONB metadata column + GIN index for filtered queries
- `ON CONFLICT DO UPDATE` for idempotent re-ingestion

**Principle:** The cheapest RAG system retrieves only useful, authorized, current evidence.

---

## Chapter 06 — Model Selection and Evaluation

**Model Selection Scorecard (Weighted):**

| Dimension | Weight |
|---|---|
| Task quality | 25% |
| Groundedness | 15% |
| Cost | 15% |
| Latency | 10% |
| Tool use | 10% |
| Safety behavior | 10% |
| Data/privacy fit | 10% |
| Operational fit | 5% |

**Model Portfolio Pattern:** Use multiple models for different task types within one platform:
- **Haiku/small:** Classification, routing, short extraction, high-volume scoring
- **Sonnet/balanced:** RAG generation, tool use, structured output, most workflows
- **Opus/large:** Complex multi-document reasoning, extended thinking, architecture review

**When NOT to Use an LLM:**
- Rule can be expressed deterministically
- Data is structured and SQL works
- Mathematical calculation required
- Lookup from a known table
- Real-time data access needed (use tools)
- Latency requirement < 100ms for simple logic

**LoRA vs Full Fine-Tuning:**

| | Full Fine-Tuning | LoRA | QLoRA |
|---|---|---|---|
| GPU required | Very high | Moderate | Low–moderate |
| Trainable params | 100% | ~1–5% | ~1–5% |
| Multiple adapters | No | Yes | Yes |
| Best for | Strategic model | Most adaptation | Resource-constrained |

**Principle:** Use the cheapest model that passes the quality, safety, latency, and governance gate.

---

## Chapter 07 — Agentic AI Fundamentals

**The Agent Loop:**
```
Goal → Observe State → Reason/Plan → Act (Tool or Model) → Observe Result → [repeat] → Final Output
```

**What Separates Agents from LLM Calls:**
- **State:** Agents maintain information across steps
- **Tools:** Agents can take actions beyond text generation
- **Memory:** Agents can access past context
- **Planning:** Agents can decompose goals into steps
- **Termination conditions:** Agents have stop criteria

**S0→S4 Autonomy Model:**

| Level | Description | Example |
|---|---|---|
| S0 | Human does everything; AI assists | Draft suggestion, human writes |
| S1 | AI proposes; human approves each action | Agent recommends; human clicks approve |
| S2 | AI acts within narrow scope; human reviews periodically | Auto-classify tickets; human reviews batch |
| S3 | AI acts autonomously; human reviews anomalies | Auto-respond to routine queries |
| S4 | AI acts autonomously in production | Reserved for proven, fully bounded workflows |

**Tool Authorization Invariant:**
> The model decides WHICH tool to call. Deterministic code decides WHETHER the call is permitted.

**Agent Cost Controls:**
- `max_steps` — always set; non-negotiable
- `max_tool_calls` — per-step and cumulative
- `max_tokens_per_step` — context budget guard
- `max_cost_usd` — spend ceiling
- Stop on: no-result from RAG, repeated identical tool call, error threshold exceeded

---

## Chapter 08 — Agent Architecture Patterns

**The 14-Pattern Catalog:**

| Pattern | When to Use |
|---|---|
| Single-Agent | Simple, self-contained task |
| Tool-Using Agent | Needs live data or external actions |
| Planner-Executor | Complex decomposable task |
| Router-Agent | Multiple specialized handlers |
| Supervisor-Worker | Parallel specialized subtasks |
| Critic-Reviewer | Output quality matters; self-checking |
| Reflection Loop | Iterative improvement needed |
| Human Approval Gate | High-impact or regulated action |
| Retrieval-Augmented | Knowledge-intensive task |
| Memory-Enabled | Multi-session personalization |
| Event-Driven | Triggered by external signals |
| Deterministic+Agent | Hybrid: rules first, AI for edge cases |
| Multi-Agent | Cross-domain parallel investigation |
| Hierarchical | Portfolio of nested workflows |

**Pattern Selection Rule:**
- Default to the simplest pattern that solves the problem
- Multi-agent is only justified when specialization creates measurable accuracy improvement
- Complexity must be justified by evaluation evidence, not architectural ambition

**Tool-Using Agent — Critical Design:**
```python
# WRONG: Model decides whether to authorize
if model_says_allowed:
    execute_tool()

# RIGHT: Deterministic code authorizes
if user_role in ALLOWED_ROLES[tool_name]:
    execute_tool()
```

**Supervisor-Worker Pattern:** Workers are narrow functions; supervisor synthesizes. In production: run workers concurrently, synthesis prompt must say "use only provided evidence," keep supervisor focused on integration not re-investigation.

---

## Chapter 09 — LangGraph for Enterprise Agents

**LangGraph Core Concepts:**

| Concept | Purpose |
|---|---|
| `TypedDict` State | Explicit schema for all workflow data |
| `StateGraph` | Graph definition: nodes + edges |
| `add_node()` | Register a function as a workflow step |
| `add_conditional_edges()` | Route based on state content |
| `interrupt_before/after` | HITL pause point |
| `PostgresSaver` | Durable checkpointing for resumability |
| `update_state()` | Inject human decision into paused graph |
| `stream(None, config)` | Resume from checkpoint |

**The HITL Pattern:**
```python
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_approval_node"]
)
# First invocation runs until interrupt
for event in app.stream(initial_state, config): ...
# Human reviews and decides...
app.update_state(config, {"approval_status": "approved"})
# Resume from checkpoint
for event in app.stream(None, config): ...
```

**State Design Principles:**
1. Put everything needed for resumability into state
2. Use `Optional[str]` for fields that may not be set yet
3. Track `step_count` and `max_steps` explicitly
4. Track `errors: list[dict]` — never raise unhandled exceptions in nodes
5. Include cost tracking fields (`total_cost_tokens`)

**Kill Switch Pattern:** Use `checkpoint_and_pause`, not hard termination — hard kill leaves orphaned state in PostgresSaver.

**Anti-Patterns:**
- Tool authorization inside routing functions (use tool gateway)
- Approval via email (use interrupt + resume)
- Global mutable state (use TypedDict)
- Uncapped loops (always set `max_steps`)

---

## Chapter 10 — Model Context Protocol (MCP)

**MCP Mental Model:**
> MCP is an enterprise integration architecture pattern — a governed protocol for connecting AI systems to tools, resources, and data sources.

**MCP is NOT:**
- A replacement for the RAG pipeline
- An API management layer
- The agent architecture itself

**Three Participants:**
- **Host:** The AI application (e.g., Claude Desktop, custom app)
- **Client:** MCP client inside the host; manages connection to servers
- **Server:** Exposes tools, resources, prompts, and roots

**Transport Types:**

| Transport | Use Case | Governance |
|---|---|---|
| stdio | Local subprocess; developer tools | Cannot be centrally monitored |
| HTTP/SSE (Streamable HTTP) | Remote servers; enterprise deployment | API gateway, centralized auth |

**Architecture Rule:** Local stdio servers are for developer productivity. Enterprise capabilities belong on remote servers behind controlled network boundaries.

**Authentication:** Remote MCP servers use **OAuth 2.0**. Enterprise identity providers (Okta, Azure AD) can serve as authorization server. Scopes represent tool-level access rights.

**Capability Registry (Enterprise Pattern):**
```yaml
tools:
  - name: get_device_telemetry
    risk_tier: 2
    data_classification: internal
    approval_required: false
    version: "1.2"
```

**Sampling:** Allows servers to request model completions — enables server-side summarization and multi-step server reasoning. Risk: recursive behavior, unclear user consent, uncontrolled cost.

---

## Chapter 11 — Amazon Bedrock

**Bedrock is Two Things:**
- **Runtime layer:** Model invocation API (Converse, InvokeModel)
- **Control plane:** Governance, routing, knowledge bases, agents, guardrails, evaluation

**API Decision:**

| API | Use When |
|---|---|
| `Converse` | Chat/multi-turn; provider-agnostic message format |
| `ConverseStream` | Same but streaming |
| `InvokeModel` | Model-specific request/response format |
| `InvokeModelWithResponseStream` | Model-specific streaming |

**Model Families on Bedrock:**
Claude (Anthropic), Titan/Nova (Amazon), Llama (Meta), Mistral, Command R (Cohere), AI21 Jamba

**Inference Patterns:**
- **On-demand:** Variable workloads; pay per token; can throttle
- **Cross-region inference profiles:** Automatic regional routing for availability and throughput
- **Application inference profiles:** Cost attribution by team/workflow/cost center
- **Provisioned throughput:** Reserved capacity for predictable high-volume
- **Batch inference:** Async S3→model→S3 for offline workloads at lower cost

**Streaming Guardrail Warning:** In streaming mode, partial tokens may appear before guardrail evaluation completes on the full response. Use synchronous invocation for high-risk regulated workflows.

**VPC Best Practice:** Use VPC Interface Endpoints (PrivateLink) for `bedrock-runtime` to keep traffic off the public internet. Enable private DNS — no code changes required.

**Principle:** Cost is architecture. Every Bedrock decision (model choice, context size, streaming, provisioned) has a cost implication.

---

## Chapter 12 — Bedrock Knowledge Bases

**Bedrock KB is Managed RAG.** RAG quality principles (Chapter 4) still apply — the platform manages infrastructure, not quality.

**Sync Modes:**

| Mode | How It Works | Best For |
|---|---|---|
| Manual | Admin triggers | Low-change, controlled content |
| Scheduled | Time-based (hourly/daily/nightly) | Predictable cadence |
| Event-driven | Source system notifies on change | High-frequency, compliance-critical |

**FM-Based (Smart) Parsing:** Uses Claude as the document parser — extracts tables, charts, images in PDFs, multi-column layouts. Higher cost; essential for complex structured documents.

**Multi-Tenancy Patterns:**

| Pattern | Isolation | Ops Overhead |
|---|---|---|
| Separate KB per tenant | Strongest | High |
| Shared KB + metadata filter | Good (if governance is strict) | Low |

**Critical Rule:** Tenant isolation must be enforced at the vector store query level (`filter={"tenant_id": "acme"}`), never by the model or post-retrieval.

**Reranking:** Bedrock supports Cohere Rerank. Use selectively — adds latency and cost. Most valuable when semantic similarity scores cluster tightly (ambiguous queries).

**Principle:** Managed RAG is still RAG. RAG quality is still AI quality.

---

## Chapter 13 — Bedrock Agents

**Build Time vs Runtime:**
- **Build time:** Define action groups, associate knowledge bases, set instructions, configure guardrails
- **Runtime:** Agent receives input, orchestrates tool calls, accesses knowledge bases, returns response

**Fulfillment Patterns:**

| Pattern | When to Use |
|---|---|
| Lambda fulfillment | Straightforward authorized actions |
| Return control | Application needs auth, approval, UX, transaction boundaries |

**Action Group Testing Strategy:**
```
Schema validation → Lambda unit tests → Authorization tests →
Integration tests (staging) → Agent-in-the-loop tests → Golden dataset tests
```

**Forbidden Action Test:** Always test that the agent does NOT call high-risk tools without approval. Include these in every golden dataset.

**Multi-Agent Collaboration:** Bedrock supports supervisor + sub-agents. Use when subtasks require different knowledge bases or tool sets. Each sub-agent has its own instructions, tools, and guardrails.

**Code Execution Action Group:** Built-in sandboxed Python execution. Enable only when workflow genuinely benefits from in-agent computation. Treat outputs as model artifacts — validate before business use.

**Bedrock Agents vs LangGraph:**

| Dimension | Bedrock Agents | LangGraph |
|---|---|---|
| State management | Managed sessions | Explicit TypedDict |
| Checkpointing | Not built-in | PostgresSaver |
| Custom routing | Limited | Full conditional edges |
| HITL durability | Limited | `interrupt_before/after` |
| AWS-native ops | Yes | Requires additional infra |

---

## Chapter 14 — Bedrock Guardrails

**Guardrail Policy Types:**

| Policy | What It Does |
|---|---|
| Content filters | Block harmful content by category and strength (low/medium/high) |
| Denied topics | Block specific business-prohibited subjects |
| Word filters | Block specific terms or phrases |
| PII detection | Detect, mask, or block personally identifiable information |
| Sensitive info | Custom regex patterns for domain-specific identifiers |
| Contextual grounding | Detect hallucinations vs provided source |
| Automated reasoning | Logic-based policy checking |

**Grounding Check Thresholds (0–1 scale):**
- 0.5–0.6: Lenient — editorial/creative workflows
- 0.7 (default): Balanced — general enterprise assistants
- 0.8–0.9: Strict — regulated policy workflows, legal, compliance

**Important:** Grounding checks evaluate whether the answer matches the provided source — not whether the source is correct. High grounding score on a bad source still produces wrong answers.

**ApplyGuardrail API:** Evaluate content without model invocation. Use to pre-screen user input, retrieved documents, and tool outputs as a platform-level content safety service.

**Streaming + Guardrails:** In streaming mode, guardrail evaluation may occur on the complete response after generation — partial tokens may reach the client before a block. For regulated workflows: use synchronous mode.

**Image Content Moderation:** Content filters apply to image inputs for vision-capable models. Always enable for workflows accepting user-uploaded images.

**Placement Rule:**
```
User Input → [Input Guardrail] → Context → Model → [Output Guardrail] → Tool Auth → User
```

---

## Chapter 15 — AI Evaluation and Testing

**The Evaluation Pyramid:**
```
Business KPIs (highest, slowest to measure)
    ↑
User acceptance (accepted, edited, rejected, escalated)
    ↑
Agent/workflow evaluation (tool selection, approval correctness)
    ↑
Generation quality (groundedness, correctness, safety)
    ↑
Retrieval quality (Recall@K, Precision@K, MRR, nDCG)
    ↑
Component tests (unit tests for each service)
```

**Retrieval Metrics:**

| Metric | Formula | What It Measures |
|---|---|---|
| Recall@K | `|relevant ∩ top_K| / |relevant|` | Did we find all relevant docs? |
| Precision@K | `|relevant ∩ top_K| / K` | What fraction of results are relevant? |
| MRR | `1 / rank_of_first_relevant` | How high is the first relevant result? |
| nDCG@K | Discount by rank position | Quality-weighted ranked retrieval |

**LLM-as-Judge Pattern:**
- Judge at `temperature=0.0` for consistency
- Separate **safety threshold** (e.g., 0.98) from **quality threshold** (e.g., 0.86)
- Safety failure blocks release even if average quality is above threshold
- Calibrate judge scores against human labels before trusting at scale

**Golden Dataset Requirements:**
- Representative production cases
- Edge cases and near-miss cases
- Forbidden action cases (safety gate)
- Cross-tenant denial cases (security gate)
- Missing evidence cases (model must acknowledge, not hallucinate)
- Injection attempt cases

**Synthetic Data Generation:** Use LLMs to generate question variants from source documents. Quality rule: human SME review required before synthetic cases enter the official dataset.

**Inter-Rater Agreement:** Before scaling human evaluation, measure inter-rater agreement. Cohen's Kappa > 0.6 = substantial; Krippendorff's Alpha > 0.67 = minimum acceptable. Low agreement = rubric is unclear, not reviewer error.

**Release Gate Pattern:**
```yaml
release_gate:
  quality_score_min: 0.86
  safety_score_min: 0.98     # Separate and stricter
  tool_accuracy_min: 0.95
  p95_latency_ms_max: 6000
  cost_per_successful_task_max_usd: 0.05
  block_on_critical_failure: true
```

---

## Chapter 16 — Claude Architecture

**The Messages API Mental Model:**
```python
client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    system="[System prompt — stable, cacheable]",
    messages=[
        {"role": "user", "content": [content_blocks...]},
        {"role": "assistant", "content": [...]},  # For multi-turn
    ]
)
```

**Content Block Types:** text, image (base64 or URL), document (for citations), tool_use, tool_result

**Model Tier Routing:**

| Tier | Latency/Cost | Best For |
|---|---|---|
| Haiku | Fastest / cheapest | Classification, extraction, routing, scoring |
| Sonnet | Balanced | RAG generation, tool use, most production |
| Opus | Slowest / highest | Multi-doc reasoning, architecture review |

**Tool Use Loop (Multi-Turn):**
1. Send request with tool definitions
2. Model returns `tool_use` blocks (stop_reason="tool_use")
3. Execute each tool (with authorization)
4. Return ALL `tool_result` blocks in ONE user message
5. Model continues until stop_reason="end_turn"

**Prompt Caching:** Mark large stable blocks with `cache_control: {"type": "ephemeral"}`. Monitor `cache_read_input_tokens` vs `cache_creation_input_tokens`. Cache lifetime: ~5 minutes inactivity.

**Extended Thinking:** `thinking: {"type": "enabled", "budget_tokens": N}`. `max_tokens` must exceed `budget_tokens`. Response includes `thinking` type blocks before `text` blocks. Use for architecture reviews, complex multi-step reasoning — not for standard workflows.

**Citations:** Enable per document with `"citations": {"enabled": True}`. Incompatible with strict JSON structured output. Always verify the user can access each cited source.

**Production Lessons:**
- Context dumping (all documents) costs 8× more than targeted RAG with no quality gain
- Tool sprawl to 14 tools degraded selection quality; narrow to 4–6 task-relevant tools
- Prompt injection bypassed security prompts — authorization belongs in the tool layer

---

## Chapter 17 — NVIDIA AI Infrastructure

**Three Layers:**

| Layer | Tool | Purpose |
|---|---|---|
| Model packaging | **NIM** | Deployable model microservices with OpenAI-compatible API |
| Serving orchestration | **Triton** | Multi-framework inference server; metrics, batching, ensembles |
| LLM optimization | **TensorRT-LLM** | Quantization, KV cache, speculative decoding, parallelism |

**NGC (NVIDIA GPU Cloud):** Source for NIM containers (`nvcr.io/nim/...`), model weights, CUDA tools. Mirror to private registry for security scanning before production use.

**Speculative Decoding:**
1. Small draft model generates K candidate tokens quickly
2. Large target model validates all K tokens in one parallel forward pass
3. Accept tokens up to first rejection; continue from target model's correction
- Best for: predictable output patterns, high-bandwidth GPU, latency-primary SLOs
- Not for: low acceptance rate (creative), memory-constrained environments

**LoRA Serving Patterns:**
- **Merged model:** Adapter baked into base model — zero inference overhead; one deployment per adapter
- **Dynamic adapter loading:** Base model shared; adapters loaded per request/tenant — more complex, lower cost at scale

**GPU FinOps Rule:** GPUs are not cheaper because you own them. They are cheaper only when you keep them productively used. Minimum utilization target: 40%.

**Self-Host Decision:**

| Use Case | Prefer Managed | Prefer Self-Hosted |
|---|---|---|
| Data must stay on-prem | — | ✓ |
| Variable workloads | ✓ | — |
| Cost at very high scale | — | ✓ |
| GPU expertise available | — | ✓ |
| Fast start needed | ✓ | — |

**Concurrent Load Testing Key Insight:** The gap between sequential p95 latency and concurrent p95 latency is the KV cache pressure signal. Sharp degradation above a concurrency level marks the effective batch capacity limit.

---

## Chapter 18 — Enterprise AI Architecture Patterns

**The 12 Platform Components:**

| Component | Responsibility |
|---|---|
| AI Gateway | Single entry point; auth, routing, cost attribution, trace |
| Model Router | Policy-based model selection by task type and data class |
| Prompt Registry | Versioned, owned, approved, evaluated prompt templates |
| Context Builder | Permission-filtered context assembly with token budget |
| RAG Platform | Governed retrieval with freshness, ACLs, citations |
| MCP/Tool Gateway | Schema validation, auth, risk tiers, audit |
| Agent Runtime | Stateful orchestration with HITL and checkpointing |
| Guardrail Service | Safety and policy enforcement layer |
| Evaluation Service | Golden datasets, LLM judge, CI/CD gate |
| Observability Plane | Trace, metrics, cost, quality, feedback |
| FinOps Layer | Budget enforcement, chargeback, cost dashboards |
| Human Approval Workflow | Structured approval for high-impact actions |

**Context Truncation Strategies:**

| Strategy | Use When |
|---|---|
| `summarize_oldest` | Multi-turn conversation; recent context matters most |
| `drop_lowest_score` | RAG workflows; lower-quality chunks dropped first |
| `fail_on_overflow` | Regulated workflows; partial context worse than no answer |
| `semantic_compress` | Quality over cost/latency |

**AWS Security Stack for AI:**
- **VPC Endpoints:** Keep Bedrock traffic off public internet; no code changes with private DNS
- **IAM Permission Boundaries:** Cap gateway role max permissions even if policy is misconfigured
- **SCPs:** Org-level controls — deny Bedrock from unauthorized accounts, restrict to approved regions

**Streaming Gateway:** `X-Accel-Buffering: no` header prevents nginx from buffering event streams. Disconnect event must propagate to provider within ~500ms to prevent abandoned token cost. TTFT (time to first token) is the primary streaming UX metric.

**Production Lesson:** Without a gateway, model sprawl appears within months — two teams building the same Bedrock integration independently, no shared cost visibility, discovered only at month-end billing.

---

## Chapter 19 — AI Security and Governance

**AI Threat Model Categories:**
- Prompt injection (direct and indirect through retrieved content)
- Data exfiltration through model outputs
- Tool abuse and privilege escalation
- RAG permission violations (cross-tenant data access)
- Model behavior manipulation
- Supply chain risks (model cards, training data)

**Defense in Depth:**
```
Identity → Tenant Policy → Input Guardrail → Permission-Filtered RAG →
Tool Authorization → Output Guardrail → Audit Log
```

**RAG Security Invariant:** Authorization happens BEFORE retrieved content reaches the model. Filter at the database query level — not after retrieval, not by the model.

**Tool Risk Tiers:**

| Tier | Type | Authorization |
|---|---|---|
| 1–2 | Read-only | Role check; no approval |
| 3 | Write (low-impact) | Role check; no approval |
| 4 | Write (medium-impact) | Role check + approval |
| 5 | Write (high-impact) | Named approver + approval packet |
| 6 | Decision support only | No AI execution ever |

**Red-Team Dataset Must Include:**
- Direct injection attempts
- Indirect injection through retrieved documents
- Tool abuse (requesting unauthorized write actions)
- Cross-tenant data requests
- Jailbreak attempts
- Multimodal injection (text in images)

**Prompt Injection Rule:** The model may comply with embedded instructions. The tool gateway and authorization layer must not — regardless of what the model requests.

**Data Classification → Model Routing:**
```yaml
restricted_data:
  external_model_allowed: false
  require_private_inference: true
```

**Kill Switches:** Every AI system needs disable switches for: model route, prompt version, tool, MCP server, agent workflow, RAG source, streaming, tenant access.

---

## Chapter 20 — AI Observability and Operations

**AI Trace Schema (Required Fields):**
```json
{
  "trace_id": "unique per request",
  "tenant_id": "who made the request",
  "workflow_id": "which workflow",
  "model_provider": "which model",
  "prompt_id": "which prompt version",
  "rag.document_ids": ["what was retrieved"],
  "tools": [{"name": "tool", "authorized": true, "latency_ms": 180}],
  "guardrails.input_intervention": false,
  "approval_required": true,
  "cost_usd": 0.31,
  "latency_ms": 4200,
  "evaluation_score": 0.91
}
```

**RAG Observability Alerts:**

| Alert | Signal | Root Cause |
|---|---|---|
| `rag.no_result` | Zero chunks returned | KB sync failure or bad query |
| `rag.stale_sources` | Documents past freshness SLA | Ingestion pipeline failure |
| `rag.high_permission_filter` | Many docs excluded | ACL misconfiguration |
| `rag.low_citation_support` | Citation score < 0.6 | Retrieval quality degraded |

**Streaming Telemetry:**
- **TTFT (time to first token):** Primary UX metric; target p95 < 1000ms
- **Abandonment rate:** % of streams cancelled before completion; >15% = investigate
- **Abandoned token cost:** Track separately from completed stream cost for FinOps

**User Feedback Signals (Strongest to Weakest):**
1. ESCALATED — user judged AI output untrustworthy
2. REJECTED — discarded output
3. EDITED — used but modified; edit distance matters
4. THUMBS_DOWN — explicit negative signal
5. ABANDONED — left without using
6. THUMBS_UP — explicit positive
7. ACCEPTED with zero edits — candidate for golden dataset positive example

**Agent Trace Fields:** state_transitions per step, tool_calls with authorized flag and params, loop_count, stop_reason. Upward trend in loop_count signals prompt or knowledge base degradation.

**Production Lesson:** A fluent answer can be wrong. A 200 OK can be harmful. API uptime is not quality telemetry.

---

## Chapter 21 — AI FinOps and Cost Optimization

**The Right Metric:**
> Cost per successful, safe, useful business workflow — not cost per token.

**Complete AI Cost Stack:**
```
Model inference + RAG retrieval + Embeddings + Reranking + Tools + Guardrails +
Evaluation + Streaming overhead + Multimodal processing + Infrastructure + Human review
```

**Cost Metrics Hierarchy:**

| Metric | Audience |
|---|---|
| Cost per token | Engineering |
| Cost per request | Platform |
| Cost per completed task | Operations |
| Cost per accepted output | Product |
| Cost per resolved case | Business |
| Cost per tenant | FinOps |

**Model Routing for Cost:**
```yaml
routes:
  - task_type: classification
    model: haiku
    max_cost_usd: 0.001
  - task_type: support_draft
    model: sonnet
    max_cost_usd: 0.03
  - task_type: executive_brief
    model: opus
    max_cost_usd: 0.25
    human_review_required: true
```

**EWMA Cost Drift Detection:**
- Use exponentially weighted moving average to detect gradual cost increases
- Static thresholds miss slow drift; EWMA adapts to the baseline
- Alert when observed value exceeds `baseline × alert_multiplier` (e.g., 1.5×)
- Apply to: cost per request, agent step count, prompt token count

**Prompt Caching Economics:**
- Cache savings = uncached repeated input cost − cache write cost − cache read cost
- Typical: cache read ≈ 10% of input cost; cache write ≈ 125% of input cost
- Break-even at ~3+ cache reads per write

**Streaming Cost Risks:**
- Client cancels → server keeps generating → billed tokens user never sees
- Fix: propagate disconnect event to provider within ~500ms
- Track abandoned stream cost separately in FinOps dashboard

**Agent Loop Cost Controls:**
```yaml
agent_budget:
  max_steps: 6
  max_tool_calls: 4
  max_total_tokens: 30000
  max_cost_usd: 0.50
```

**GPU Utilization Rule:** <40% average utilization means managed cloud is likely cheaper than self-hosted, even at scale.

---

## Chapter 22 — Enterprise AI Delivery and Operating Model

**The Operating Model Answers:**
- Who decides which use cases are worth building?
- Who owns knowledge quality?
- Who approves high-risk workflows?
- Who measures ROI?
- Who supports after launch?
- How do pilots become products?
- How do products become platforms?

**AI Product Lifecycle:**
```
Intake → Discovery → Architecture → Prototype → Evaluation Gate →
Pilot → Production Readiness → Launch → Operate → Measure → Improve/Retire
```

**Team Topologies for AI:**

| Team Type | Owns |
|---|---|
| Stream-aligned (product) | Business workflow, user experience, KPI |
| AI Platform | Gateway, RAG, tools, eval, observability, FinOps |
| Enabling | Helps product teams adopt platform patterns |
| Complicated-subsystem | Specialized retrieval, model serving, security |
| Governance | Policy, risk review, approvals |

**Risk-Tiered Governance:**
- Tier 1–2: Self-service checklist + async architect spot-check (30 min)
- Tier 3: Standard 48-hour review using pre-approved patterns
- Tier 4–5: Full security, legal, architecture review with explicit risk acceptance

**Production Readiness Gate (Must-Haves):**
- Named owner (business + product + platform + support + knowledge + tool API)
- Risk tier approved; data classification complete
- Evaluation gate passed (quality + safety + cost)
- Runbook written; rollback plan defined
- Budget approved; observability dashboard ready

**Operating Cadence:**

| Meeting | Frequency | Purpose |
|---|---|---|
| Architecture review | Weekly | New use cases and changes |
| Evaluation review | Biweekly | Quality, safety, regressions |
| Portfolio review | Monthly | Prioritize, scale, retire |
| Model/cost review | Monthly | Routing, budgets, vendors |
| Executive steering | Quarterly | Strategy, funding, risk |

**Knowledge Ownership Rule:** RAG quality is not owned by the model team. It is owned by the knowledge owners and the platform together. Freshness SLA must be defined per source, not globally.

**Production Lesson:** Pilots stall without owners. Platform teams must operate like product teams — adoption rate is a first-class KPI.

---

## Chapter 23 — AI Strategy, ROI, and Executive Decision-Making

**AI Strategy vs AI Theater:**

| AI Theater | AI Strategy |
|---|---|
| Many demos | Capability-first thinking |
| Unclear owners | Named owners |
| No ROI model | Measurable value pools |
| No adoption plan | Adoption plan + change management |
| Vendor-led roadmap | Vendor strategy with exit criteria |

**Value Pools:** Revenue growth, cost reduction, risk reduction, speed, quality, personalization, resilience, decision leverage.

**Risk-Adjusted ROI Formula:**
```
ROI =
(adoption-adjusted value + risk reduction value - total AI operating cost - change management cost)
/ (total AI operating cost + platform investment)
```

**Key Variables:**
- `adoption_rate` is the hardest to forecast and the most impactful — model multiple scenarios (30%, 50%, 70%, 85%)
- `implementation_cost` drives payback period — often underestimated
- `risk_reduction_value` is real but hard to quantify — use incident cost avoidance as proxy

**Portfolio Stage Gates:** idea → discovery → prototype → evaluation → pilot → production → scale → optimize → retire

**Scale Criteria:** KPI improvement measurable + adoption real + quality above threshold + safety controlled + cost per workflow acceptable + support model exists + platform reuse possible

**Stop Criteria:** No owner + no measurable KPI + low adoption + cost exceeds value + risk unacceptable + deterministic automation is better

**Vendor Lock-In Is Not Only Contract Lock-In:**
- Workflow lock-in: workflow designed around vendor-specific behavior
- Prompt lock-in: format incompatible with other providers
- Evaluation lock-in: dataset built for one model's behavior
- Observability lock-in: traces not exportable

**Mitigation:** AI gateway + model router + evaluation portability + MCP tool abstraction + OpenTelemetry traces

**Build vs Buy Decision:**

| Situation | Approach |
|---|---|
| Commodity workflow | Buy |
| Differentiating capability | Build |
| Complex field workflow | FDE |
| Specialized infrastructure | Partner |
| Unclear value | Prototype first |

**Board Narrative Structure:** Where AI creates advantage → investment maps to strategy → value realized → risks controlled → reusable capabilities → operating model → competitor context → decisions needed → what will stop

**Principle:** AI strategy is choosing what NOT to build.

---

## Chapter 24 — Capstone: Enterprise Agentic Operations Platform

**The Platform Rule:**
> AI can investigate, retrieve, summarize, recommend, and draft.
> AI cannot execute high-impact production actions without deterministic authorization and human approval.

**Architecture Decision Records:**

| ADR | Decision | Rationale |
|---|---|---|
| ADR-001 | AI Gateway as single entry point | Routing, cost attribution, governance, security |
| ADR-002 | RAG for knowledge; tools for live state | Reduces stale responses; improves auditability |
| ADR-003 | Human approval for high-impact actions | Blast radius control; accountability; compliance |
| ADR-004 | Portfolio model routing | Cost, data placement, capability fit, fallback |

**The LangGraph Capstone Agent:**
```python
# IncidentState TypedDict → 7 nodes → PostgresSaver + interrupt_after HITL
# Nodes: classify_intent → retrieve_runbooks → query_telemetry →
#         assess_customer_impact → generate_recommendation →
#         create_approval_packet [INTERRUPT] → finalize_after_approval
#                                           OR → draft_response
```

**Evaluation Gate Requirements:**
- `quality_score_min: 0.86`
- `safety_score_min: 0.98` (separate, stricter threshold)
- `tool_accuracy_min: 0.95`
- `approval_correctness_min: 0.99` (firmware rollback must always flag approval)
- `block_on_critical_failure: true` (injection, cross-tenant = immediate block)

**Golden Dataset Must Include:**
1. Normal cases (happy path)
2. Ambiguous telemetry (model must express uncertainty)
3. Missing evidence (must acknowledge, not hallucinate)
4. Prompt injection through symptom field
5. Cross-tenant access attempt
6. Executive brief request

**Capstone KPIs:**

| Metric | Target |
|---|---|
| Mean time to triage | −30–50% |
| Executive brief prep time | −60% |
| Support draft acceptance | >70% |
| Unauthorized production actions | 0 |
| Cost per incident investigation | Under budget |

**Production Lesson:** The agent is not the product. The product is faster, safer incident resolution. Recommendation latency was not from model quality but from the approval workflow surfacing in the wrong UI. 60% resolution time drop came from embedding the recommendation in the existing ticketing system — no model change.

---

## Chapter 25 — AI Architect Career Roadmap and Final Playbook

**The Five Career Stages:**
```
Practitioner → AI Engineer → AI Platform Engineer → AI Architect → AI Transformation Leader
```

| Stage | Outcome |
|---|---|
| Practitioner | Can build useful demos and prototypes |
| AI Engineer | Can build production AI services |
| AI Platform Engineer | Can build reusable AI platform capabilities |
| AI Architect | Can design enterprise AI systems and guide teams |
| Transformation Leader | Can lead enterprise AI transformation |

**The VASE Interview Framework:**
- **V**alue — What business outcome matters?
- **A**rchitecture — What system pattern solves it?
- **S**afety — What controls are required?
- **E**vidence — How do we measure success?

**Interview Dimensions:** Technical depth + Architecture judgment + Business thinking + Leadership + Communication. Senior interviews reward structured judgment more than tool-name memorization.

**The STAR+Architecture Format:**
```
Situation: business/technical context
Task: what needed to change
Action: architecture and leadership decisions
Result: measurable outcome (numbers)
Architecture: pattern, tradeoff, controls, lessons learned
```

**GitHub Portfolio Must Show:**
- Architecture diagrams (not just descriptions)
- Working Python scaffolds (runnable, not pseudocode)
- Realistic YAML configs
- Evaluation datasets with test cases
- Component tests that pass
- Executive briefs

**90-Day Plan:**
- Days 1–30: Foundation, capability map, first RAG prototype, evaluation dataset v0
- Days 31–60: Gateway skeleton, model routing, prompt registry, RAG metadata standard, trace schema
- Days 61–90: Pilot one workflow, run evaluation, cost model, executive brief, scale decision memo

**Weekly Operating System:**
- Study one technical topic
- Improve one portfolio artifact
- Review one architecture pattern
- Write one executive summary
- Run one lab or test

---

## Quick Reference: Key Decision Tables

### When to Use What

| Need | Solution |
|---|---|
| Static knowledge, grounding | RAG |
| Live data, real-time state | Tools/MCP |
| Style/format consistency at scale | LoRA fine-tuning |
| Current factual knowledge | RAG (not fine-tuning) |
| Sequential multi-step workflow | LangGraph |
| AWS-managed orchestration | Bedrock Agents |
| Cost optimization | Model router + prompt caching |
| Data sovereignty | Self-hosted / private inference |
| Deterministic safety controls | Guardrails + tool authorization |
| Production quality proof | Golden dataset evaluation |

### Architecture Anti-Patterns

| Anti-Pattern | The Fix |
|---|---|
| Prompts as security boundaries | Authorization in code (ToolGateway) |
| Model decides authorization | Deterministic role-based policy |
| Every team builds their own LLM client | AI Gateway as single control point |
| Context dumping (all documents) | Retrieval with permission filters |
| No evaluation before production | Golden dataset + release gate |
| Agent with no step limit | `max_steps`, `max_cost_usd` always set |
| Approval via email | LangGraph interrupt + resume |
| RAG without source ownership | Named knowledge owner per domain |
| Cost visible only at invoice | Per-workflow, per-tenant cost attribution |
| All workflows on largest model | Model routing by task complexity |

---

## Final Pratik's Principles (25 Canonical)

1. Technology is a means, not the mission.
2. Complexity is a liability unless it creates measurable business value.
3. Start with deterministic systems. Add AI only where uncertainty creates value.
4. Every AI system should have an off switch.
5. Humans should remain accountable for high-impact decisions.
6. The cheapest model that solves the business problem is usually the correct model.
7. A 90% accurate model deployed safely today may create more value than a 99% model delivered next year.
8. AI is an amplifier, not a strategy.
9. Retrieval quality is AI quality.
10. Do not use prompts as security boundaries.
11. Use RAG for knowledge and tools for live state.
12. If it cannot be measured, it cannot be managed.
13. Production AI is a system, not a model.
14. Trust is an architecture feature.
15. ROI is the forcing function that separates useful AI from demo AI.
16. Agents recommend; systems authorize.
17. Context is architecture.
18. Evaluation is the quality system for probabilistic software.
19. Observability is the operating system for trust.
20. Cost per successful workflow beats cost per token.
21. Governance should accelerate safe delivery, not block it.
22. A platform is valuable only when teams reuse it.
23. Pilots are not products.
24. Strategy is choosing what not to build.
25. The AI architect's job is to turn capability into accountable value.

---

*Study Guide generated from: The AI Architect & Practitioner Bootcamp — Chapters 00–25*  
*Author: Pratik Desai*
