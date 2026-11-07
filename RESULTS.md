# LeanCode benchmark results

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | Agent pass | Scored pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 01-sum-last-item | no | 4014 | yes | yes | 757 | 1 | 52.19 |
| 02-palindrome-normalize | no | 4569 | no | no | 4391 | 6 | 46.78 |
| 03-median-even | no | 6305 | yes | yes | 784 | 1 | 30.06 |
| 04-average-empty | no | 4077 | yes | yes | 774 | 1 | 25.38 |
| 05-stable-unique | no | 6303 | yes | yes | 733 | 1 | 28.41 |
| 06-discount-rounding | no | 6462 | no | no | 4244 | 6 | 56.05 |
| 07-parse-bool | no | 4242 | no | no | 828 | 1 | 25.91 |
| 08-fibonacci-zero | no | 4779 | yes | yes | 967 | 1 | 26.77 |
| 09-invoice-tax-multifile | no | 4380 | no | no | 4280 | 6 | 41.69 |
| 10-user-lookup-multifile | no | 4413 | yes | yes | 822 | 1 | 26.86 |
| 11-js-slugify | no | 4611 | no | no | 4050 | 6 | 66.19 |
| 12-js-retry-delay | no | 5181 | no | no | 5125 | 6 | 58.92 |
| 13-env-port-multifile | no | 0 | no | no | 3091 | 6 | 34.62 |
| 14-csv-total-multifile | no | 0 | yes | no | 702 | 1 | 10.30 |
| 15-cache-expiry-multifile | no | 4113 | yes | yes | 883 | 1 | 31.23 |
| 16-js-retry-classifier | no | 4419 | yes | no | 1574 | 2 | 38.88 |
| 17-safe-path-multifile | no | 5822 | yes | no | 752 | 1 | 36.05 |
| 18-pagination-multifile | no | 4011 | yes | yes | 790 | 1 | 30.42 |

- Tasks: 18
- Naive pass rate: 0/18 (0.0%)
- LeanCode pass rate: 8/18 (44.4%)
- Naive total tokens: 77701
- LeanCode total tokens: 35547
- Token reduction: 54.3%
