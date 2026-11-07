# LeanCode benchmark results

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 09-invoice-tax-multifile | no | 4386 | no | 4496 | 6 | 53.95 |
| 13-env-port-multifile | no | 0 | no | 3007 | 6 | 31.89 |
| 14-csv-total-multifile | no | 0 | no | 691 | 1 | 10.16 |
| 16-js-retry-classifier | no | 4422 | no | 3403 | 6 | 51.02 |

- Tasks: 4
- Naive pass rate: 0/4 (0.0%)
- LeanCode pass rate: 0/4 (0.0%)
- Naive total tokens: 8808
- LeanCode total tokens: 11597
- Token reduction: -31.7%
