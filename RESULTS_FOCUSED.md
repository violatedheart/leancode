# LeanCode benchmark results

Model: `qwen3.5:4b`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 07-parse-bool | no | 5068 | no | 5493 | 6 | 74.25 |
| 17-safe-path-multifile | no | 5862 | no | 4163 | 6 | 68.91 |

- Tasks: 2
- Naive pass rate: 0/2 (0.0%)
- LeanCode pass rate: 0/2 (0.0%)
- Naive total tokens: 10930
- LeanCode total tokens: 9656
- Token reduction: 11.7%
