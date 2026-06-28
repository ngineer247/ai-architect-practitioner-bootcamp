"""
Chapter 03 — Lab 1: Production Prompt Template
The AI Architect & Practitioner Bootcamp

A versioned, testable production prompt loader with:
  - YAML registry backend
  - Variable validation before render
  - Status enforcement (approved/draft/deprecated)
  - Lightweight regression test runner
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


class PromptRegistryError(Exception):
    pass


@dataclass
class PromptTemplate:
    name: str
    version: str
    template: str
    description: str
    owner: str
    variables: list[str] = field(default_factory=list)
    status: str = "draft"
    deprecated: bool = False
    rollback_version: Optional[str] = None

    def __post_init__(self):
        detected = re.findall(r"\{\{(\w+)\}\}", self.template)
        if not self.variables:
            self.variables = detected
        undeclared = set(detected) - set(self.variables)
        if undeclared:
            raise ValueError(f"Template contains undeclared variables: {undeclared}")

    def render(self, allow_draft: bool = False, **kwargs) -> str:
        if self.deprecated:
            raise PromptRegistryError(
                f"Prompt '{self.name}' v{self.version} is deprecated."
            )
        if not allow_draft and self.status != "approved":
            raise PromptRegistryError(
                f"Prompt '{self.name}' status is '{self.status}' — "
                "only approved prompts allowed in production"
            )
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise PromptRegistryError(f"Missing variables: {missing}")

        result = self.template
        for key, value in kwargs.items():
            result = result.replace("{{" + key + "}}", str(value))

        remaining = re.findall(r"\{\{(\w+)\}\}", result)
        if remaining:
            raise PromptRegistryError(f"Unrendered variables: {remaining}")
        return result

    def test(self, test_cases: list[dict]) -> dict:
        results = []
        for i, case in enumerate(test_cases):
            try:
                rendered = self.render(allow_draft=True, **case)
                results.append({"case": i, "status": "pass", "length": len(rendered)})
            except Exception as e:
                results.append({"case": i, "status": "fail", "error": str(e)})
        passed = sum(1 for r in results if r["status"] == "pass")
        return {
            "template": self.name,
            "version": self.version,
            "total": len(test_cases),
            "passed": passed,
            "failed": len(test_cases) - passed,
            "results": results,
        }


class PromptLoader:
    """Load and render prompts from a YAML registry file."""

    def __init__(self, registry_path: str = "prompts.yaml"):
        data = yaml.safe_load(Path(registry_path).read_text(encoding="utf-8"))
        self._registry: dict[str, PromptTemplate] = {}
        for p in data.get("prompts", []):
            tmpl = PromptTemplate(
                name=p["name"],
                version=p["version"],
                template=p["template"],
                description=p.get("description", ""),
                owner=p.get("owner", "unassigned"),
                variables=p.get("variables", []),
                status=p.get("status", "draft"),
                deprecated=p.get("deprecated", False),
                rollback_version=p.get("rollback_version"),
            )
            self._registry[tmpl.name] = tmpl

    def get(self, name: str) -> PromptTemplate:
        if name not in self._registry:
            raise PromptRegistryError(f"Prompt '{name}' not found in registry")
        return self._registry[name]

    def render(self, name: str, allow_draft: bool = False, **kwargs) -> str:
        return self.get(name).render(allow_draft=allow_draft, **kwargs)

    def list_prompts(self) -> list[str]:
        return sorted(self._registry.keys())


if __name__ == "__main__":
    loader = PromptLoader("prompts.yaml")
    print("Available prompts:", loader.list_prompts())

    rendered = loader.render(
        "support_policy_answer",
        allow_draft=False,
        user_question="What is the refund policy?",
        retrieved_context="Refunds accepted within 30 days of purchase."
    )
    print("\nRendered prompt:\n", rendered)
