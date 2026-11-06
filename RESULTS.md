# LeanCode benchmark results

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 01-sum-last-item | no | 4020 | yes | 555 | 1 | 27.80 |
| 02-palindrome-normalize | no | 5964 | no | 2889 | 6 | 36.89 |
| 03-median-even | no | 6269 | yes | 595 | 1 | 24.88 |
| 04-average-empty | no | 4077 | yes | 562 | 1 | 21.55 |
| 05-stable-unique | no | 6303 | yes | 550 | 1 | 23.72 |
| 06-discount-rounding | no | 6462 | no | 4202 | 6 | 38.17 |
| 07-parse-bool | no | 4254 | no | 4488 | 6 | 36.44 |
| 08-fibonacci-zero | no | 4788 | yes | 851 | 1 | 23.41 |
| 09-invoice-tax-multifile | no | 4386 | no | 3557 | 6 | 35.24 |
| 10-user-lookup-multifile | no | 4410 | yes | 635 | 1 | 22.02 |
| 11-js-slugify | no | 4707 | no | 2437 | 6 | 38.31 |
| 12-js-retry-delay | no | 5250 | no | 2781 | 6 | 40.89 |
| 13-env-port-multifile | no | 0 | no | 1978 | 6 | 16.69 |
| 14-csv-total-multifile | no | 0 | no | 401 | 1 | 5.81 |
| 15-cache-expiry-multifile | no | 4113 | no | 554 | 1 | 22.31 |
| 16-js-retry-classifier | no | 528 | no | 1872 | 6 | 17.48 |
| 17-safe-path-multifile | no | 5822 | no | 447 | 1 | 25.89 |
| 18-pagination-multifile | no | 4011 | yes | 479 | 1 | 22.12 |

- Tasks: 18
- Naive pass rate: 0/18 (0.0%)
- LeanCode pass rate: 7/18 (38.9%)
- Naive total tokens: 75364
- LeanCode total tokens: 29833
- Token reduction: 60.4%
