"""Tests for Chapter 07 Lab 1: Agent Loop"""
import pytest
from unittest.mock import MagicMock
from agent_loop import AgentTool, AgentState, run_agent, search_incidents_tool


def make_mock_client(responses: list[str]):
    """Return a mock model client that yields responses in sequence."""
    client = MagicMock()
    call_count = {"n": 0}

    def complete(**kwargs):
        idx = min(call_count["n"], len(responses) - 1)
        call_count["n"] += 1
        resp = MagicMock()
        resp.text = responses[idx]
        resp.usage.total_tokens = 100
        return resp

    client.complete = complete
    return client


def test_agent_finishes_with_done_signal():
    client = make_mock_client(['{"done": true, "answer": "Found 2 incidents."}'])
    state = run_agent(
        goal="Find incidents for product X",
        tools=[],
        model_client=client,
        system_prompt="You are an analyst.",
    )
    assert state.final_answer == "Found 2 incidents."
    assert state.step_count == 1


def test_agent_calls_tool_then_finishes():
    responses = [
        '{"tool": "search_incidents", "params": {"product": "device-core"}}',
        '{"done": true, "answer": "Found INC-001 and INC-002."}',
    ]
    client = make_mock_client(responses)

    tools = [AgentTool(
        name="search_incidents",
        description="Search incidents by product.",
        execute=search_incidents_tool,
    )]

    state = run_agent(
        goal="Find device-core incidents",
        tools=tools,
        model_client=client,
        system_prompt="You are an analyst.",
        user_role="analyst",
    )

    assert state.final_answer is not None
    assert len(state.tool_calls) == 1
    assert state.tool_calls[0]["tool"] == "search_incidents"


def test_agent_respects_max_steps():
    # Always returns a tool call — should hit max_steps
    client = make_mock_client(['{"tool": "search_incidents", "params": {"product": "x"}}'])
    tools = [AgentTool(
        name="search_incidents",
        description="Search.",
        execute=search_incidents_tool,
    )]
    state = run_agent(
        goal="Loop forever",
        tools=tools,
        model_client=client,
        system_prompt=".",
        user_role="analyst",
        max_steps=3,
    )
    assert state.step_count >= 3
    assert state.final_answer is None


def test_unknown_tool_recorded_as_error():
    client = make_mock_client(['{"tool": "nonexistent_tool", "params": {}}'])
    state = run_agent(
        goal="Use unknown tool",
        tools=[],
        model_client=client,
        system_prompt=".",
        user_role="analyst",
    )
    assert any("Unknown tool" in e["error"] for e in state.errors)


def test_unauthorized_role_recorded_not_raised():
    client = make_mock_client([
        '{"tool": "search_incidents", "params": {"product": "x"}}',
        '{"done": true, "answer": "Could not search — access denied."}',
    ])
    tools = [AgentTool(
        name="search_incidents",
        description="Search.",
        execute=search_incidents_tool,
    )]
    state = run_agent(
        goal="Search as unauthorized user",
        tools=tools,
        model_client=client,
        system_prompt=".",
        user_role="guest",  # Not in authorized roles
        max_steps=5,
    )
    # Agent should have received a denial observation and continued
    denied = [o for o in state.observations if "DENIED" in o]
    assert len(denied) >= 1
