# LeanCode benchmark results

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | Agent pass | Scored pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 17-safe-path-multifile | no | 3609 | no | no | 3300 | 6 | 45.50 |

- Tasks: 1
- Naive pass rate: 0/1 (0.0%)
- LeanCode pass rate: 0/1 (0.0%)
- Naive total tokens: 3609
- LeanCode total tokens: 3300
- Token reduction: 8.6%
