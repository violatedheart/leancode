# LeanCode repository rules

- Keep all inference local through the configured OpenAI-compatible endpoint. Do not add cloud model fallbacks or model frameworks.
- Deterministic code does repository indexing, BM25 localization, path checks, syntax checks, test execution, compression, and token accounting. The model gets only selected code and four constrained tools: `find`, `read`, `edit`, and `test`.
- Prompts are stateless. Rebuild a five-line-or-shorter state card; never replay chat history in LeanCode. Keep system prompt plus schema under 300 estimated tokens, each input at or below 1500 tokens, each output at or below 400 tokens, context 4096, six total steps, and the configured total token budget.
- Use exact unique search/replace edits only. Refuse paths outside the repository. Syntax-check with cached Tree-sitter grammars and run only the configured test command. Never offer arbitrary shell or network access to the model.
- Compress test results to failing names, assertions, and at most eight repository frames. Cap each tool result near 400 tokens. Stop as soon as tests pass or the budget is exhausted.
- Run the unit suite after changes: `python -m pytest` (or `python -m unittest discover -s tests -v` when pytest is unavailable). Run and record the paired benchmark only when the local model server is available; never fabricate measured results.
- Each completed milestone must have passing tests and a Git commit. Update `README.md`, `RESULTS.md`, and these rules when behavior changes.
