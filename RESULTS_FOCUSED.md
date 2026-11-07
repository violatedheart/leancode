# LeanCode benchmark results

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 02-palindrome-normalize | no | 4587 | no | 5133 | 6 | 61.83 |
| 09-invoice-tax-multifile | no | 4386 | no | 4031 | 6 | 46.34 |
| 13-env-port-multifile | no | 0 | no | 2973 | 6 | 28.01 |
| 14-csv-total-multifile | no | 0 | no | 691 | 1 | 8.61 |
| 17-safe-path-multifile | no | 5822 | no | 715 | 1 | 32.95 |

- Tasks: 5
- Naive pass rate: 0/5 (0.0%)
- LeanCode pass rate: 0/5 (0.0%)
- Naive total tokens: 14795
- LeanCode total tokens: 13543
- Token reduction: 8.5%
