"""
Chapter 07 — Lab 1: Basic Agent Loop
The AI Architect & Practitioner Bootcamp

Implements the fundamental agent loop: decide → act → observe → repeat.
This is the foundation that all Chapter 08 patterns and the Chapter 09
LangGraph implementation build upon.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class AgentTool:
    """A tool the agent can request."""
    name: str
    description: str
    execute: Callable[[dict, str], str]  # (params, user_role) -> result


@dataclass
class AgentState:
    goal: str
    observations: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    final_answer: Optional[str] = None
    step_count: int = 0
    max_steps: int = 10
    total_cost_tokens: int = 0


def run_agent(
    goal: str,
    tools: list[AgentTool],
    model_client,
    system_prompt: str,
    user_role: str = "analyst",
    max_steps: int = 10,
) -> AgentState:
    """
    Minimal agent loop: decide → act → observe → repeat.

    The model decides which tool to call (or to finish).
    The loop executes the tool, adds the result to state, and continues.
    Explicit stop conditions prevent runaway execution.
    """
    state = AgentState(goal=goal, max_steps=max_steps)

    tool_descriptions = "\n".join([
        f"  {t.name}: {t.description}" for t in tools
    ])
    tool_registry = {t.name: t for t in tools}

    while state.step_count < state.max_steps:
        state.step_count += 1

        observation_text = "\n".join(state.observations) or "No observations yet."
        prompt = f"""Goal: {goal}

Available tools:
{tool_descriptions}

Observations so far:
{observation_text}

Decide the next action. Respond with EXACTLY one of:
1. A tool call as JSON: {{"tool": "<name>", "params": {{...}}}}
2. A final answer: {{"done": true, "answer": "<answer>"}}
"""
        response = model_client.complete(
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.0,
        )
        state.total_cost_tokens += getattr(response.usage, "total_tokens", 0)

        try:
            decision = json.loads(response.text.strip())
        except json.JSONDecodeError:
            state.errors.append({
                "step": state.step_count,
                "error": "Model did not return valid JSON",
                "raw": response.text[:200],
            })
            break

        if decision.get("done"):
            state.final_answer = decision.get("answer", "")
            break

        tool_name = decision.get("tool")
        tool_params = decision.get("params", {})

        if tool_name not in tool_registry:
            state.errors.append({
                "step": state.step_count,
                "error": f"Unknown tool: {tool_name}",
            })
            break

        try:
            tool_result = tool_registry[tool_name].execute(tool_params, user_role)
            state.tool_calls.append({
                "step": state.step_count,
                "tool": tool_name,
                "params": tool_params,
                "result": tool_result[:500],
            })
            state.observations.append(
                f"Step {state.step_count} — {tool_name}: {tool_result}"
            )
        except PermissionError as e:
            state.errors.append({
                "step": state.step_count,
                "tool": tool_name,
                "error": f"Authorization denied: {e}",
            })
            state.observations.append(
                f"Step {state.step_count} — {tool_name}: DENIED — {e}"
            )
        except Exception as e:
            state.errors.append({"step": state.step_count, "tool": tool_name, "error": str(e)})
            break

    if state.step_count >= state.max_steps and not state.final_answer:
        state.final_answer = None  # Caller handles escalation

    return state


# ─── Example tools (replace with real implementations) ──────────────────────

AUTHORIZED_ROLES = {
    "search_incidents": {"analyst", "support_l2", "operations"},
    "get_runbook":      {"analyst", "support_l2", "operations"},
}


def search_incidents_tool(params: dict, user_role: str) -> str:
    if user_role not in AUTHORIZED_ROLES["search_incidents"]:
        raise PermissionError(f"Role '{user_role}' not authorized")
    product = params.get("product", "unknown")
    return json.dumps({
        "incidents": ["INC-001", "INC-002"],
        "product": product,
        "count": 2,
    })


def get_runbook_tool(params: dict, user_role: str) -> str:
    if user_role not in AUTHORIZED_ROLES["get_runbook"]:
        raise PermissionError(f"Role '{user_role}' not authorized")
    return json.dumps({
        "runbook": "Heartbeat Failure v3",
        "steps": ["1. Check firmware", "2. Verify network", "3. Restart service"],
    })


if __name__ == "__main__":
    print("Agent loop module loaded.")
    print("Use run_agent() with a model client to execute the agent.")
    print("\nAvailable example tools:")
    print("  search_incidents(product, region)")
    print("  get_runbook(incident_type)")
