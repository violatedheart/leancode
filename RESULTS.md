# LeanCode feature ablation sweep

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Each lane runs the same tasks and budget; hidden tests are injected only after an agent run.

| Feature set | Pass rate | Total tokens | Tokens per solved task | Time (s) |
|---|---:|---:|---:|---:|
| all-on | n/a | n/a | n/a | n/a |
| without-reproduce | n/a | n/a | n/a | n/a |
| without-hypothesize | n/a | n/a | n/a | n/a |
| without-best-of-three | n/a | n/a | n/a | n/a |
| without-playbook | n/a | n/a | n/a | n/a |
| without-notes | n/a | n/a | n/a | n/a |

Keep a feature enabled by default only when the all-on lane improves pass rate or tokens per solved task over the lane with that feature ablated.

## Run status

- all-on: not run: local OpenAI-compatible endpoint unavailable
- without-reproduce: not run: local OpenAI-compatible endpoint unavailable
- without-hypothesize: not run: local OpenAI-compatible endpoint unavailable
- without-best-of-three: not run: local OpenAI-compatible endpoint unavailable
- without-playbook: not run: local OpenAI-compatible endpoint unavailable
- without-notes: not run: local OpenAI-compatible endpoint unavailable
