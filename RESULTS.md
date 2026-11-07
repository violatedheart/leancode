# LeanCode benchmark results

Model: `qwen3.5:4b`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 01-sum-last-item | yes | 682 | yes | 778 | 1 | 13.70 |
| 02-palindrome-normalize | no | 5168 | yes | 3176 | 5 | 55.80 |
| 03-median-even | yes | 4302 | no | 4510 | 6 | 67.39 |
| 04-average-empty | yes | 691 | yes | 2780 | 5 | 39.33 |
| 05-stable-unique | yes | 715 | yes | 854 | 1 | 14.62 |
| 06-discount-rounding | no | 6043 | yes | 3648 | 6 | 71.58 |
| 07-parse-bool | no | 4790 | no | 5121 | 6 | 67.45 |
| 08-fibonacci-zero | yes | 3781 | yes | 2013 | 2 | 33.61 |
| 09-invoice-tax-multifile | no | 4928 | yes | 4912 | 6 | 65.53 |
| 10-user-lookup-multifile | yes | 819 | yes | 1746 | 2 | 23.83 |
| 11-js-slugify | no | 6542 | no | 3431 | 6 | 62.38 |
| 12-js-retry-delay | no | 6194 | no | 4010 | 6 | 61.66 |
| 13-env-port-multifile | yes | 1491 | no | 3367 | 6 | 50.16 |
| 14-csv-total-multifile | no | 1483 | no | 786 | 1 | 20.34 |
| 15-cache-expiry-multifile | no | 5041 | no | 3939 | 6 | 65.75 |
| 16-js-retry-classifier | no | 5304 | no | 4192 | 6 | 63.48 |
| 17-safe-path-multifile | no | 5862 | no | 4160 | 6 | 67.64 |
| 18-pagination-multifile | no | 5972 | yes | 1637 | 2 | 43.08 |

- Tasks: 18
- Naive pass rate: 7/18 (38.9%)
- LeanCode pass rate: 9/18 (50.0%)
- Naive total tokens: 69808
- LeanCode total tokens: 55060
- Token reduction: 21.1%
