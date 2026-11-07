# LeanCode benchmark results

Model: `qwen3.5:4b`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 01-sum-last-item | yes | 685 | yes | 1582 | 2 | 26.45 |
| 02-palindrome-normalize | no | 5152 | yes | 3167 | 5 | 57.08 |
| 03-median-even | no | 5966 | no | 4509 | 6 | 73.64 |
| 04-average-empty | yes | 1674 | yes | 2073 | 3 | 32.59 |
| 05-stable-unique | yes | 710 | yes | 767 | 1 | 12.92 |
| 06-discount-rounding | no | 6042 | yes | 897 | 1 | 39.56 |
| 07-parse-bool | yes | 1915 | no | 4922 | 6 | 53.73 |
| 08-fibonacci-zero | yes | 2318 | no | 4751 | 6 | 51.45 |
| 09-invoice-tax-multifile | no | 4924 | no | 4966 | 6 | 70.81 |
| 10-user-lookup-multifile | yes | 722 | yes | 1650 | 2 | 23.16 |
| 11-js-slugify | no | 5302 | no | 2965 | 6 | 57.52 |
| 12-js-retry-delay | no | 6194 | no | 4785 | 6 | 64.19 |
| 13-env-port-multifile | yes | 1491 | no | 3321 | 6 | 52.08 |
| 14-csv-total-multifile | no | 1483 | no | 2009 | 3 | 32.47 |
| 15-cache-expiry-multifile | no | 5041 | yes | 1726 | 2 | 41.00 |
| 16-js-retry-classifier | yes | 3478 | no | 4219 | 6 | 56.97 |
| 17-safe-path-multifile | no | 5862 | no | 4163 | 6 | 68.73 |
| 18-pagination-multifile | no | 5972 | no | 4596 | 6 | 67.84 |

- Tasks: 18
- Naive pass rate: 8/18 (44.4%)
- LeanCode pass rate: 7/18 (38.9%)
- Naive total tokens: 64931
- LeanCode total tokens: 57068
- Token reduction: 12.1%
