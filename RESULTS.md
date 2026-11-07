# LeanCode benchmark results

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 01-sum-last-item | no | 4014 | yes | 686 | 1 | 35.59 |
| 02-palindrome-normalize | no | 4581 | no | 5554 | 6 | 86.69 |
| 03-median-even | no | 6282 | yes | 728 | 1 | 44.34 |
| 04-average-empty | no | 4077 | yes | 701 | 1 | 38.84 |
| 05-stable-unique | no | 4068 | yes | 669 | 1 | 38.61 |
| 06-discount-rounding | no | 6462 | no | 3585 | 6 | 73.67 |
| 07-parse-bool | no | 4254 | no | 3536 | 6 | 67.76 |
| 08-fibonacci-zero | no | 4779 | yes | 2353 | 3 | 52.80 |
| 09-invoice-tax-multifile | no | 4386 | no | 3872 | 6 | 61.19 |
| 10-user-lookup-multifile | no | 4410 | yes | 752 | 1 | 37.58 |
| 11-js-slugify | no | 4611 | no | 2794 | 6 | 53.80 |
| 12-js-retry-delay | no | 5175 | no | 3541 | 6 | 61.56 |
| 13-env-port-multifile | no | 0 | no | 3189 | 6 | 38.67 |
| 14-csv-total-multifile | no | 0 | no | 658 | 1 | 10.09 |
| 15-cache-expiry-multifile | no | 4113 | yes | 838 | 1 | 31.19 |
| 16-js-retry-classifier | no | 4419 | no | 2990 | 6 | 49.86 |
| 17-safe-path-multifile | no | 5822 | no | 675 | 1 | 37.06 |
| 18-pagination-multifile | no | 4011 | yes | 718 | 1 | 30.91 |

- Tasks: 18
- Naive pass rate: 0/18 (0.0%)
- LeanCode pass rate: 8/18 (44.4%)
- Naive total tokens: 75464
- LeanCode total tokens: 37839
- Token reduction: 49.9%
