# LeanCode benchmark results

Model: `qwen3.5:4b`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | Agent pass | Scored pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 01-sum-last-item | yes | 442 | yes | yes | 0 | 0 | 4.00 |
| 02-palindrome-normalize | yes | 739 | yes | yes | 0 | 0 | 6.09 |
| 03-median-even | yes | 479 | yes | yes | 0 | 0 | 7.25 |
| 04-average-empty | yes | 475 | yes | yes | 0 | 0 | 3.33 |
| 05-stable-unique | yes | 503 | yes | yes | 0 | 0 | 5.12 |
| 06-discount-rounding | yes | 488 | yes | yes | 0 | 0 | 6.94 |
| 07-parse-bool | yes | 618 | yes | yes | 0 | 0 | 5.91 |
| 08-fibonacci-zero | yes | 708 | yes | yes | 0 | 0 | 3.59 |
| 09-invoice-tax-multifile | no | 3654 | yes | yes | 0 | 0 | 12.83 |
| 10-user-lookup-multifile | yes | 541 | yes | yes | 0 | 0 | 6.08 |
| 11-js-slugify | yes | 977 | yes | yes | 0 | 0 | 9.45 |
| 12-js-retry-delay | no | 6751 | yes | yes | 0 | 0 | 14.78 |
| 13-env-port-multifile | no | 425 | yes | yes | 0 | 0 | 4.81 |
| 14-csv-total-multifile | no | 314 | yes | yes | 0 | 0 | 4.03 |
| 15-cache-expiry-multifile | yes | 493 | yes | yes | 0 | 0 | 4.94 |
| 16-js-retry-classifier | no | 484 | yes | yes | 0 | 0 | 4.16 |
| 17-safe-path-multifile | yes | 557 | yes | yes | 0 | 0 | 6.92 |
| 18-pagination-multifile | yes | 476 | yes | yes | 0 | 0 | 4.45 |

- Tasks: 18
- Naive pass rate: 13/18 (72.2%)
- LeanCode pass rate: 18/18 (100.0%)
- Naive total tokens: 19124
- LeanCode total tokens: 0
- Token reduction: 100.0%
