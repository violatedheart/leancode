# LeanCode benchmark results

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 13-env-port-multifile | no | 0 | no | 2973 | 6 | 31.72 |
| 14-csv-total-multifile | no | 0 | no | 691 | 1 | 9.94 |
| 17-safe-path-multifile | no | 5822 | no | 715 | 1 | 36.84 |

- Tasks: 3
- Naive pass rate: 0/3 (0.0%)
- LeanCode pass rate: 0/3 (0.0%)
- Naive total tokens: 5822
- LeanCode total tokens: 4379
- Token reduction: 24.8%
