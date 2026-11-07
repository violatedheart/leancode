# LeanCode benchmark results

Model: `qwen3.5:4b`. Every lane runs in a fresh temporary copy. Hidden tests are injected only while scoring.

| Task | Naive pass | Naive tokens | LeanCode pass | LeanCode tokens | Steps | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| 11-js-slugify | no | 6222 | no | 3265 | 6 | 37.95 |
| 12-js-retry-delay | no | 6496 | no | 2819 | 6 | 29.44 |
| 16-js-retry-classifier | yes | 578 | no | 3508 | 6 | 29.59 |
| 18-pagination-multifile | yes | 471 | no | 1344 | 2 | 16.45 |

- Tasks: 4
- Naive pass rate: 2/4 (50.0%)
- LeanCode pass rate: 0/4 (0.0%)
- Naive total tokens: 13767
- LeanCode total tokens: 10936
- Token reduction: 20.6%
