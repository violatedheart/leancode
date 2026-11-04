# LeanCode repository rules

- Keep all inference local through the configured OpenAI-compatible endpoint. Do not add cloud model fallbacks or model frameworks.
- Deterministic code does repository indexing, BM25 localization, path checks, syntax checks, test execution, compression, and token accounting. The model gets only selected code and four constrained tools: `find`, `read`, `edit`, and `test`.
- Prompts are stateless. Rebuild a five-line-or-shorter state card; never replay chat history in LeanCode. Keep system prompt plus schema under 300 estimated tokens, each input at or below 1500 tokens, each output at or below 400 tokens, context 4096, six total steps, and the configured total token budget.
- Use exact unique search/replace edits only. Refuse paths outside the repository. Syntax-check with cached Tree-sitter grammars and run only the configured test command. Never offer arbitrary shell or network access to the model.
- Compress test results to failing names, assertions, and at most eight repository frames. Cap each tool result near 400 tokens. Stop as soon as tests pass or the budget is exhausted.
- Run the unit suite after changes: `python -m pytest` (or `python -m unittest discover -s tests -v` when pytest is unavailable). Run and record the paired benchmark only when the local model server is available; never fabricate measured results.
- Each completed milestone must have passing tests and a Git commit. Update `README.md`, `RESULTS.md`, and these rules when behavior changes.
- Preserve the expert phase order: understand task criteria and repo notes; localize by BM25 plus callers/callees; reproduce only when baseline tests are green; hypothesize after an unsuccessful fast patch; verify locally; then review the patch before finishing.
- Keep each phase prompt constrained and below 300 tokens for its fixed prefix/schema. Keep the prompt stateless, the input at 1500 tokens, the completion at 400 tokens, and the total run at six model calls and the configured task budget.
- Reproduction tests are temporary, at most 30 lines, and must fail on an assertion before a source patch is attempted. Remove the test and newly created bytecode after the check.
- Restrict edits to a selected symbol and 40 changed lines. Reject edits to existing tests, skip/xfail changes, unrelated paths, and duplicate patch hashes. Best-of-three candidates run only in scratch copies below `.leancode/`.
- Optional expert features stay off by default until `leancode bench --sweep` shows a pass-rate or tokens-per-solved-task improvement. Record measured feature-ablation results; report unavailable endpoints as not run.
- Export prompt/completion pairs only from passing runs to `.leancode/traces.jsonl`; do not include fine-tuning code or upload traces.
