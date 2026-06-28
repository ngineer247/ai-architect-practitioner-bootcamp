# Lab 1: Production Prompt Template

**Chapter 03 — Prompt Engineering and Context Design**

## What You Build

A production-grade prompt management system with:
- YAML-based versioned prompt registry
- Variable validation before render
- Status enforcement (approved prompts only in production)
- Regression test runner

## Quick Start

```bash
pip install -r requirements.txt
python prompt_loader.py          # Render an example prompt
pytest tests/ -v                 # Run all tests
```

## Tasks

1. Add a new prompt to `prompts.yaml` with at least 2 variables
2. Run the regression test suite against it
3. Try rendering a draft prompt without `allow_draft=True` — observe the error
4. Add a `rollback_version` field and verify it is stored in the registry
5. Add an `evaluation.last_score` field to the YAML schema and extend the loader

## Key Concepts

- `{{variable}}` syntax for template variables
- `status: approved` required for production render
- `rollback_version` documents the safe fallback
- `PromptRegistryError` on missing variables prevents broken prompts reaching the model

## From the Book

Chapter 03, Section 10: Prompt Templates and Section 11: Prompt Versioning
