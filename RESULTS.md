# LeanCode benchmark results

Model: `qwen3.5:4b`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 01-sum-last-item | yes | 441 | yes | 686 | 1 | 7.34 |
| 02-palindrome-normalize | yes | 701 | no | 3547 | 6 | 28.72 |
| 03-median-even | yes | 473 | yes | 796 | 1 | 9.86 |
| 04-average-empty | yes | 471 | yes | 742 | 1 | 7.06 |
| 05-stable-unique | yes | 521 | yes | 730 | 1 | 9.28 |
| 06-discount-rounding | yes | 494 | yes | 775 | 1 | 7.98 |
| 07-parse-bool | yes | 622 | no | 950 | 1 | 10.47 |
| 08-fibonacci-zero | yes | 709 | yes | 1700 | 3 | 16.34 |
| 09-invoice-tax-multifile | no | 3625 | no | 4261 | 6 | 34.06 |
| 10-user-lookup-multifile | yes | 530 | yes | 829 | 1 | 8.22 |
| 11-js-slugify | yes | 975 | no | 3156 | 6 | 30.73 |
| 12-js-retry-delay | no | 6515 | no | 2851 | 6 | 30.14 |
| 13-env-port-multifile | no | 449 | no | 3140 | 6 | 29.89 |
| 14-csv-total-multifile | no | 314 | no | 2696 | 6 | 23.86 |
| 15-cache-expiry-multifile | yes | 505 | no | 3370 | 6 | 25.56 |
| 16-js-retry-classifier | yes | 577 | no | 3438 | 6 | 28.28 |
| 17-safe-path-multifile | yes | 554 | no | 1143 | 2 | 17.27 |
| 18-pagination-multifile | yes | 471 | no | 1344 | 2 | 16.16 |

- Tasks: 18
- Naive pass rate: 14/18 (77.8%)
- LeanCode pass rate: 7/18 (38.9%)
- Naive total tokens: 18947
- LeanCode total tokens: 36154
- Token reduction: -90.8%
