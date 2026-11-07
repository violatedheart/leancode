# LeanCode benchmark results

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 02-palindrome-normalize | no | 4581 | no | 5618 | 6 | 84.95 |
| 09-invoice-tax-multifile | no | 4383 | no | 3864 | 6 | 55.28 |
| 13-env-port-multifile | no | 0 | no | 3197 | 6 | 40.91 |
| 14-csv-total-multifile | no | 0 | no | 658 | 1 | 10.52 |
| 15-cache-expiry-multifile | no | 4113 | yes | 838 | 1 | 31.31 |
| 17-safe-path-multifile | no | 5822 | no | 675 | 1 | 37.67 |
| 18-pagination-multifile | no | 4011 | yes | 718 | 1 | 31.80 |

- Tasks: 7
- Naive pass rate: 0/7 (0.0%)
- LeanCode pass rate: 2/7 (28.6%)
- Naive total tokens: 22910
- LeanCode total tokens: 15568
- Token reduction: 32.0%
