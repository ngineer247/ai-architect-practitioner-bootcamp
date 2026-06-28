"""Tests for Chapter 03 Lab 1: Prompt Loader"""
import pytest
from pathlib import Path
from prompt_loader import PromptLoader, PromptRegistryError


@pytest.fixture
def loader(tmp_path):
    p = tmp_path / "prompts.yaml"
    p.write_text("""
prompts:
  - name: test_approved
    version: "1.0.0"
    status: approved
    owner: test
    variables: [topic]
    template: "Explain {{topic}} briefly."
    rollback_version: "0.9.0"

  - name: test_draft
    version: "2.0.0"
    status: draft
    owner: test
    variables: [input]
    template: "Draft response: {{input}}"
    rollback_version: "1.9.0"
""")
    return PromptLoader(str(p))


def test_render_approved_prompt(loader):
    result = loader.render("test_approved", topic="LangGraph")
    assert "LangGraph" in result


def test_draft_blocked_in_production(loader):
    with pytest.raises(PromptRegistryError, match="approved"):
        loader.render("test_draft", input="hello")


def test_draft_allowed_in_dev(loader):
    result = loader.render("test_draft", allow_draft=True, input="hello")
    assert "hello" in result


def test_missing_variable_raises(loader):
    with pytest.raises(PromptRegistryError, match="Missing"):
        loader.render("test_approved")


def test_unknown_prompt_raises(loader):
    with pytest.raises(PromptRegistryError, match="not found"):
        loader.get("nonexistent")


def test_list_prompts(loader):
    names = loader.list_prompts()
    assert "test_approved" in names
    assert "test_draft" in names


def test_regression_suite(loader):
    tmpl = loader.get("test_approved")
    results = tmpl.test([
        {"topic": "RAG"},
        {"topic": "LangGraph"},
        {},  # Missing variable — should fail
    ])
    assert results["passed"] == 2
    assert results["failed"] == 1
