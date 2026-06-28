# Contributing

Thank you for your interest in this project.

## What Contributions Are Welcome

**Bug reports in code:** If a lab implementation has a bug, incorrect import, or logic
error, please open an issue with the chapter number, lab name, and a description of
the problem. Include the error output if applicable.

**Clarification requests:** If a concept, diagram, or code example is unclear, open
an issue. Good questions improve the content for everyone.

**Typo and grammar fixes:** Small editorial improvements are welcome as pull requests.

## What Is Not Accepted

- Changes to architecture patterns, principles, or recommendations without discussion
- New chapters or labs not planned in the roadmap
- Dependency upgrades without testing against the existing lab code
- AI-generated content additions

## How to Submit a Bug Fix

1. Open an issue describing the problem first
2. Fork the repository
3. Make the fix in a branch named `fix/chapter-NN-description`
4. Ensure the relevant lab tests still pass: `pytest labs/chapter-NN-*/tests/`
5. Open a pull request referencing the issue

## Code Style

- Python: follow the existing style in each lab (dataclasses, type hints, docstrings)
- No external formatter required — consistency within a file matters more than
  cross-file uniformity
- Tests must pass before PR review

## Lab Testing

Each lab includes a `tests/` directory. Run tests from the lab directory:

```bash
cd labs/chapter-18-enterprise-patterns/lab1-ai-gateway
pip install -r requirements.txt
pytest tests/ -v
```

## Questions

Open an issue with the `question` label. Questions that reveal gaps in the content
are particularly valuable.
