# LeanCode benchmark results

Model: `qwen3.5:4b`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 02-palindrome-normalize | no | 5144 | yes | 3166 | 5 | 115.36 |
| 07-parse-bool | no | 3249 | no | 4949 | 6 | 60.52 |

- Tasks: 2
- Naive pass rate: 0/2 (0.0%)
- LeanCode pass rate: 1/2 (50.0%)
- Naive total tokens: 8393
- LeanCode total tokens: 8115
- Token reduction: 3.3%
