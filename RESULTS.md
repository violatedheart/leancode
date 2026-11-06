# LeanCode benchmark results

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 01-sum-last-item | no | 4017 | yes | 617 | 1 | 26.59 |
| 02-palindrome-normalize | no | 4587 | no | 4108 | 6 | 53.56 |
| 03-median-even | no | 6270 | yes | 659 | 1 | 30.38 |
| 04-average-empty | no | 4083 | yes | 639 | 1 | 26.17 |
| 05-stable-unique | no | 6302 | yes | 602 | 1 | 29.64 |
| 06-discount-rounding | no | 6463 | no | 2407 | 6 | 45.67 |
| 07-parse-bool | no | 4254 | no | 2475 | 6 | 38.22 |
| 08-fibonacci-zero | no | 4788 | yes | 1897 | 5 | 36.12 |
| 09-invoice-tax-multifile | no | 4383 | no | 2553 | 6 | 40.62 |
| 10-user-lookup-multifile | no | 4407 | yes | 686 | 1 | 25.49 |
| 11-js-slugify | no | 4710 | no | 2531 | 6 | 42.75 |
| 12-js-retry-delay | no | 5247 | no | 2497 | 6 | 42.58 |
| 13-env-port-multifile | no | 0 | no | 2387 | 6 | 24.80 |
| 14-csv-total-multifile | no | 0 | no | 552 | 1 | 7.48 |
| 15-cache-expiry-multifile | no | 4113 | yes | 1988 | 5 | 35.88 |
| 16-js-retry-classifier | no | 4473 | no | 2467 | 6 | 45.64 |
| 17-safe-path-multifile | no | 3609 | no | 618 | 1 | 26.76 |
| 18-pagination-multifile | no | 4011 | yes | 616 | 1 | 25.74 |

- Tasks: 18
- Naive pass rate: 0/18 (0.0%)
- LeanCode pass rate: 8/18 (44.4%)
- Naive total tokens: 75717
- LeanCode total tokens: 30299
- Token reduction: 60.0%
