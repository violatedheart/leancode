# LeanCode

LeanCode is a local-first command-line coding agent for small bug fixes and features. Give it a repository and a task; it finds relevant code, proposes a focused patch, and runs your test command. Its goal is to solve tasks correctly while using fewer model tokens.

The default model endpoint is Ollama on your computer. LeanCode only sends the task and selected code to the configured endpoint. The model cannot run arbitrary shell commands or access files outside the target repository.

## Requirements

- Python 3.11 or newer
- Git
- Ollama installed and a coding model pulled, or an OpenAI-compatible server such as `llama-server`
- A test runner appropriate for the repository you want LeanCode to edit

Tree-sitter language packs provide symbol indexing and syntax checks for Python and JavaScript/TypeScript. If the pack is unavailable, LeanCode falls back to Python's standard-library `ast` parser for Python files. JavaScript/TypeScript edits need an available Tree-sitter grammar.

## Install on Windows

Open PowerShell and run:

```powershell
git clone https://github.com/violatedheart/leancode.git
cd leancode
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If PowerShell blocks virtual-environment activation, use the environment's Python directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m leancode.cli doctor
```

## Install on Linux or macOS

```bash
git clone https://github.com/violatedheart/leancode.git
cd leancode
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Set up a local model

Start Ollama and pull a model that fits your machine. `leancode doctor` reports detected hardware and recommends a model size and context:

```powershell
leancode doctor
ollama pull qwen2.5-coder:7b-instruct-q4_K_M
ollama list
```

On Windows, Ollama normally runs in the background after opening the Ollama app. Confirm its local API responds before running LeanCode:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

On Linux or macOS, start Ollama if it is not already running:

```bash
ollama serve
```

In a second terminal, pull the model and confirm it is installed:

```bash
ollama pull qwen2.5-coder:7b-instruct-q4_K_M
ollama list
```

For a smaller-memory machine, use a smaller Q4 model, such as `qwen2.5-coder:1.5b-instruct-q4_0`. The quality and pass rate depend on the model. LeanCode sends Ollama a 4096-token context setting.

## Configure the model endpoint

Defaults for Ollama are:

- Base URL: `http://127.0.0.1:11434/v1`
- Model: selected by `leancode doctor`, unless you pass `--model` or set `LEANCODE_MODEL`
- API key: `ollama` (Ollama does not require a hosted API key)

PowerShell:

```powershell
$env:LEANCODE_BASE_URL = "http://127.0.0.1:11434/v1"
$env:LEANCODE_MODEL = "qwen2.5-coder:7b-instruct-q4_K_M"
$env:LEANCODE_API_KEY = "ollama"
```

Linux/macOS:

```bash
export LEANCODE_BASE_URL=http://127.0.0.1:11434/v1
export LEANCODE_MODEL=qwen2.5-coder:7b-instruct-q4_K_M
export LEANCODE_API_KEY=ollama
```

For `llama-server`, start its OpenAI-compatible API and point LeanCode at it. The model alias must match `LEANCODE_MODEL`:

```bash
llama-server -m ./models/qwen-coder-q4.gguf --alias local-coder --ctx-size 4096 --host 127.0.0.1 --port 8080
export LEANCODE_BASE_URL=http://127.0.0.1:8080/v1
export LEANCODE_MODEL=local-coder
```

The endpoint is swappable for a compatible gateway. If you configure a remote hosted endpoint, your task and selected source snippets are sent to that provider and may incur charges. Keep API keys in environment variables; do not paste them into source files or commit them.

## Use LeanCode

First go to the repository you want to change, then provide the task and its test command:

```powershell
cd C:\path\to\your\project
leancode run --repo . --task "Fix the off-by-one bug in parse_rows" --test-cmd "python -m pytest -q" --budget 6000
```

For a unittest project:

```powershell
leancode run --repo . --task "Handle an empty input in safe_average" --test-cmd "python -m unittest discover -s tests -q"
```

For a JavaScript project:

```powershell
leancode run --repo . --task "Fix retryDelay for attempt zero" --test-cmd "node --test"
```

Use `--model` to override the selected model. Use `--base-url` for a non-default compatible server, and `--budget` to change the total-token budget:

```powershell
leancode run --repo . --task "..." --test-cmd "python -m pytest -q" --model qwen2.5-coder:7b-instruct-q4_K_M --budget 6000
```

`--test-cmd` is optional, but without it LeanCode cannot verify the patch and reports it as unverified. Only the configured test command runs; the model itself has no shell tool. Run LeanCode on a working copy if you want to preserve your original repository unchanged.

## Commands

```text
leancode doctor                 Detect hardware and recommend a model
leancode run --repo . ...       Solve one coding task
leancode bench                  Compare LeanCode with the naive baseline
leancode bench --sweep          Compare workflow feature settings
leancode bench --sweep --fresh  Ignore saved sweep progress and restart
```

The benchmark uses 18 isolated tasks. The sweep runs six feature settings over those tasks and can take a while. It checkpoints each completed task in `.leancode/sweep-progress.json`, updates `RESULTS.md` as it runs, and resumes by default when you run the same command again. Use `--fresh` to discard that progress.

## Token use and logs

LeanCode limits prompts and completions, indexes code locally, and sends only selected function snippets rather than the full repository. It stops when tests pass, the step limit is reached, or the token budget is exhausted.

Per-call token usage is recorded under `.leancode/runs/`. Server usage fields are used when available; otherwise LeanCode estimates counts from text length. Full prompt tokens remain counted even when the server reports cached-prefix reuse. Passing prompt/completion pairs are exported to `.leancode/traces.jsonl` for possible future fine-tuning; no training code is included.

## Current benchmark result

Using `qwen2.5-coder:7b-instruct-q4_K_M`:

- LeanCode: **7/18 passed (38.9%)**
- Naive baseline: **0/18 passed**
- LeanCode tokens: **29,833**
- Naive baseline tokens: **75,364**
- Token reduction: **60.4%**

See [RESULTS.md](RESULTS.md) for the task-by-task table. These measurements are a baseline; the remaining failing tasks still need investigation and improvement.

## Decisions

- **Interface:** Python CLI with `argparse`; no agent framework.
- **Model runtime:** Ollama locally by default, with an OpenAI-compatible base URL and model name for swapping servers.
- **Indexing fallback:** use Tree-sitter grammars when available; use Python's built-in AST parser when the Tree-sitter pack is missing. JavaScript/TypeScript currently require Tree-sitter grammars.
- **Task workflow:** localize code first, ask the model for a small search/replace edit, run tests, and use a bounded repair loop only when needed.
- **Safety:** edits stay in the target repository and selected symbols; test execution uses only the user's configured command.
- **Feature defaults:** optional reproduce, hypothesize, best-of-three, playbook, and notes features remain opt-in until a fresh feature sweep shows a pass-rate or tokens-per-solved-task improvement.

