# LeanCode

LeanCode is a local-first CLI coding agent for small bug fixes and features. It tries one focused patch from a few relevant functions, tests it, and only enters a short repair loop if needed. The model sees selected source snippets and four constrained actions; it cannot browse files itself or run arbitrary commands.

## Install

Requires Python 3.11+, Ollama or `llama-server`, and a local coding model. Python dependencies are `httpx` and `tree-sitter-language-pack`; `pytest` is available in the development extra.

```bash
cd leancode
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

The language pack only uses parsers already present on disk during agent runs. To prepare Python and JavaScript/TypeScript grammars once during setup, run:

```bash
python -c "from tree_sitter_language_pack import download; download(['python', 'javascript', 'typescript', 'tsx'])"
```

LeanCode does not download grammars at runtime. Inference requests go only to `LEANCODE_BASE_URL` (localhost by default); all indexing, patching, syntax checks, and file operations are local. If a grammar is missing, indexing omits that language and edits in it are refused before tests run.

## Local model setup

Check available RAM and GPU, see the recommended model and copy its pull command:

```bash
leancode doctor
```

For an 8 GB RAM laptop with little or no dedicated GPU, the recommendation is a 3B 4-bit coder with a 4096-token server context. The compact fallback is `qwen2.5-coder:1.5b-instruct-q4_0`:

```bash
ollama pull qwen2.5-coder:1.5b-instruct-q4_0
OLLAMA_CONTEXT_LENGTH=4096 ollama serve
```

The default model is selected from the detected hardware; override it with `LEANCODE_MODEL` or `--model`. The 1.5B Q4 model is listed in the [Ollama model library](https://ollama.com/library/qwen2.5-coder%3A1.5b-instruct-q4_0).

For llama.cpp, download a compatible Q4 GGUF separately, then start its OpenAI-compatible server with context 4096:

```bash
llama-server -m ./models/qwen-coder-q4.gguf --alias local-coder --ctx-size 4096 --host 127.0.0.1 --port 8080
export LEANCODE_BASE_URL=http://127.0.0.1:8080/v1
export LEANCODE_MODEL=local-coder
```

`llama-server` exposes OpenAI-compatible chat completions and supports a configurable context size; see the [llama.cpp server guide](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md). A local Bifrost gateway can sit between LeanCode and either server by pointing `LEANCODE_BASE_URL` at that gateway and using the route’s model name. Keep that gateway local if project data must remain on the laptop.

LeanCode defaults to `http://127.0.0.1:11434/v1`. Optional environment variables:

```bash
export LEANCODE_BASE_URL=http://127.0.0.1:11434/v1
export LEANCODE_MODEL=qwen2.5-coder:1.5b-instruct-q4_0
export LEANCODE_API_KEY=ollama
```

## Use

```bash
leancode run --repo . --task "Fix the off-by-one bug in parse_rows" --test-cmd "python -m pytest -q" --budget 6000
```

For JavaScript/TypeScript, configure the project test command, such as `node --test`. If `--test-cmd` is omitted, LeanCode will still propose and syntax-check a patch but will report it as unverified. Tests always run with the configured command; the model has no shell tool.

```bash
leancode doctor
leancode run --repo . --task "..." [--test-cmd "..."] [--budget 6000] [--model local-coder]
leancode bench
```

Every model request is stateless. The run log at `.leancode/runs/<run-id>.jsonl` records prompt, completion, cached-prefix and total tokens. Server usage counters are preferred; when absent, LeanCode tries a local tokenizer endpoint and then estimates at four characters per token. Cached tokens remain included in total prompt tokens.

## Design and limits

- Python first, JavaScript/TypeScript next; symbol indexing and BM25 localization are local and use no LLM tokens.
- A single fast-path call sees at most three relevant function bodies. If tests fail, a stateless fallback runs up to six total model steps with `find`, `read`, `edit`, and `test` actions.
- The system prompt plus action schema is under 300 estimated tokens; each request is capped at 1500 input tokens and 400 output tokens. The model server context is configured to 4096. Default task budget is 6000 total tokens.
- Edits are unique search/replace blocks, whitespace-tolerant, syntax-checked with an already-cached Tree-sitter grammar, and retried once after a small indentation repair. Test output is reduced to failures, assertions, and at most eight repository stack frames; each tool result is capped at about 400 tokens.
- Only the configured test command runs. The model cannot execute shell commands, access paths outside `--repo`, or use network tools. Run the agent on a working copy if you need a reversible patch review.
- Pass rate and model behavior depend on the chosen local model. This project has not been calibrated with the target laptop’s GPU or local inference server in this workspace.

## Benchmark

`leancode bench` compares LeanCode with a deliberately naive full-file/full-history rewrite baseline using the same model and token budget. It runs twelve isolated tasks in fresh temporary copies, including two multi-file tasks and six separate hidden-test sets, and writes `RESULTS.md`. The initial task suites fail before any patch. Results are marked “not run” when the configured endpoint is unavailable; no synthetic pass or token figures are substituted.

Current workspace status: the 12 visible benchmark suites were verified to fail before fixes. The paired model benchmark is **not run** because no local Ollama or llama.cpp endpoint is listening here. Start the server and rerun `leancode bench` to populate pass rates and measured token reduction.

## Decisions

- **CLI and implementation:** Python 3.11+, `argparse`, and direct HTTP calls; no LangChain or agent framework.
- **Default model:** choose from detected memory, preferring Qwen2.5-Coder Q4 tags already published by Ollama; use 1.5B when memory is very limited, 3B around an 8 GB laptop, and 7B only with more headroom. The exact `doctor` output is authoritative.
- **Runtime locality:** the model endpoint defaults to localhost. Setup may install Python packages and prefetch grammars; run-time indexing, patching, syntax checks, and tests never fetch remote data. A Bifrost URL is supported for a local gateway.
- **Constrained output:** one compact JSON Schema is reused for the fast and fallback calls, with temperature zero and no conversational history. `think=false` and `num_ctx=4096` are sent to Ollama; llama.cpp context is set at server launch.
- **Edits and safety:** exact unique search/replace only; source writes stay below the target repo, and tests run only through the user-provided command. No free-form shell or network tools are exposed to the model.
- **Token accounting:** count the complete serialized prompt plus schema without discounts for cache hits. Use server usage first, tokenizer endpoint second, chars/4 estimate last; display cached-prefix reuse separately.
- **Benchmark baseline:** keep a deliberately wasteful agent that replays full history and full repository content, rewrites entire files, and uses the same local model and token budget. Hidden tests are injected only during scoring.
- **Context and steps:** use the requested 4096 server context and 1500-token input cap; count the fast-path call in the six-step total to protect the 6000-token default budget.

