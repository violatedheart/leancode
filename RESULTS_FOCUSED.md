# LeanCode benchmark results

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | Agent pass | Scored pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 17-safe-path-multifile | no | 3609 | yes | no | 726 | 1 | 32.14 |
| 18-pagination-multifile | no | 4011 | yes | yes | 751 | 1 | 26.92 |

- Tasks: 2
- Naive pass rate: 0/2 (0.0%)
- LeanCode pass rate: 1/2 (50.0%)
- Naive total tokens: 7620
- LeanCode total tokens: 1477
- Token reduction: 80.6%
