# Book State

**Last updated:** June 2026  
**Status:** All 26 chapters complete — production-quality draft

---

## Chapter Status

| Chapter | Title | Status | Python Labs | Production Lessons |
|---|---|---|---|---|
| 00 | Preface | ✅ Complete | — | — |
| 01 | Evolution of AI | ✅ Complete | — | ✅ |
| 02 | Large Language Models | ✅ Complete | Token budget estimator | ✅ |
| 03 | Prompt Engineering | ✅ Complete | PromptLoader class + tests | ✅ |
| 04 | RAG | ✅ Complete | RAG pipeline + multimodal RAG | ✅ |
| 05 | Vector Databases | ✅ Complete | pgvector search + Build vs Buy | ✅ |
| 06 | Model Selection | ✅ Complete | Scorecard + LoRA/QLoRA decision | ✅ |
| 07 | Agentic AI Fundamentals | ✅ Complete | Agent loop skeleton | ✅ |
| 08 | Agent Architecture Patterns | ✅ Complete | Tool-Using + Supervisor-Worker | ✅ |
| 09 | LangGraph for Enterprise Agents | ✅ Complete | StateGraph + PostgresSaver HITL | ✅ |
| 10 | Model Context Protocol | ✅ Complete | MCP server + LangGraph+MCP | ✅ |
| 11 | Amazon Bedrock | ✅ Complete | Converse + ConverseStream | ✅ |
| 12 | Bedrock Knowledge Bases | ✅ Complete | Retrieve + RetrieveAndGenerate | ✅ |
| 13 | Bedrock Agents | ✅ Complete | Lambda handler + InvokeAgent | ✅ |
| 14 | Bedrock Guardrails | ✅ Complete | ApplyGuardrail + Converse+guardrails | ✅ |
| 15 | AI Evaluation and Testing | ✅ Complete | LLM-as-judge + Recall@K + runner | ✅ |
| 16 | Claude Architecture | ✅ Complete | Tool loop + caching + thinking | ✅ |
| 17 | NVIDIA AI Infrastructure | ✅ Complete | NIM client + Triton + load test | ✅ |
| 18 | Enterprise AI Architecture Patterns | ✅ Complete | Gateway + prompt loader + tool gateway + eval | ✅ |
| 19 | AI Security and Governance | ✅ Complete | ToolAuthService + injection suite + RAG permissions | ✅ |
| 20 | AI Observability and Operations | ✅ Complete | AITrace + RAGTrace + FeedbackEvent + tests | ✅ |
| 21 | AI FinOps and Cost Optimization | ✅ Complete | BudgetEnforcer + WorkflowCost + EWMA + Streaming | ✅ |
| 22 | Enterprise AI Delivery and Operating Model | ✅ Complete | IntakeValidator + scorer + readiness gate | ✅ |
| 23 | AI Strategy, ROI, Executive Decision-Making | ✅ Complete | ROI model + payback + sensitivity + portfolio | ✅ |
| 24 | Capstone: Enterprise Agentic Ops Platform | ✅ Complete | Full LangGraph agent + golden dataset + eval | ✅ |
| 25 | AI Architect Career Roadmap | ✅ Complete | STAR stories + VASE + tracker | — |

---

## Lab Status

| Lab Directory | Implementation | Tests |
|---|---|---|
| chapter-03/lab1-prompt-template | ✅ prompt_loader.py | ✅ test_prompt_loader.py |
| chapter-04/lab1-rag-pipeline | ✅ rag_pipeline.py | ✅ test_rag.py |
| chapter-05/lab1-pgvector | ✅ vector_search.py | ✅ test_vector_search.py |
| chapter-07/lab1-agent-loop | ✅ agent_loop.py | ✅ test_agent_loop.py |
| chapter-09/lab4-incident-agent | ✅ incident_agent.py | ✅ test_agent.py |
| chapter-15/lab1-eval-harness | ✅ evaluator.py | ✅ test_eval.py |
| chapter-18/lab1-ai-gateway | ✅ gateway.py | ✅ test_gateway.py |
| chapter-19/lab2-tool-authorization | ✅ tool_auth.py | ✅ test_tool_auth.py |
| chapter-19/lab3-prompt-injection | ✅ run_tests.py | ✅ attacks.jsonl (10 cases) |
| chapter-19/lab4-rag-permissions | ✅ retrieval_policy.py | ✅ test_permissions.py |
| chapter-21/lab2-workflow-cost | ✅ workflow_cost.py | ✅ test_workflow_cost.py |
| chapter-21/lab5-streaming-cost | ✅ streaming_cost.py + ewma.py | — |
| chapter-24/lab4-incident-agent | ✅ Full LangGraph agent | ✅ golden_dataset.jsonl (6 cases) |

---

## Terminology and Continuity

**Production context:** All examples and lessons reference a connected device
management platform running connected device infrastructure across dozens of countries.

**Production systems (anonymized):**
- SupportIQ — AI co-pilot for support; AHT 30 min → 5 min
- TriageIQ — Incident triage automation; SLA 5 days → 5 hours
- CertifyIQ — Release certification; near-zero P1/P2 over 6 years
- DeviceIQ — Device telemetry and operations intelligence
- Managed Services Automations — Reporting and proactive alerting

**Capstone system:** Enterprise Agentic Operations Platform

**Core invariant across all agentic chapters:**
> The model recommends. Deterministic systems authorize.

**HITL pattern:** Always `interrupt_before/after` + `PostgresSaver` + `update_state()` + `stream(None, config)`. Never hard-kill.

**Cost metric:** Cost per successful, safe, useful business workflow — not cost per token.

**Autonomy model:** S0 (fully manual) → S4 (fully autonomous). Autonomy is earned through demonstrated reliability and telemetry, not granted upfront.
