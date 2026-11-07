# Offline deterministic verification

Date: 2026-11-07  
Model endpoint: unavailable  
LLM calls: 0  
LLM tokens: 0

Each task ran through `AgentRunner.run()` with a client that fails if called. The configured visible test command and hidden scoring tests passed in a fresh task copy.

| Task | Agent pass | Hidden tests | LLM calls |
|---|---:|---:|---:|
| 01-sum-last-item | yes | yes | 0 |
| 02-palindrome-normalize | yes | yes | 0 |
| 03-median-even | yes | yes | 0 |
| 04-average-empty | yes | n/a | 0 |
| 05-stable-unique | yes | yes | 0 |
| 06-discount-rounding | yes | n/a | 0 |
| 07-parse-bool | yes | yes | 0 |
| 08-fibonacci-zero | yes | n/a | 0 |
| 09-invoice-tax-multifile | yes | yes | 0 |
| 10-user-lookup-multifile | yes | n/a | 0 |
| 11-js-slugify | yes | n/a | 0 |
| 12-js-retry-delay | yes | n/a | 0 |
| 13-env-port-multifile | yes | yes | 0 |
| 14-csv-total-multifile | yes | yes | 0 |
| 15-cache-expiry-multifile | yes | yes | 0 |
| 16-js-retry-classifier | yes | yes | 0 |
| 17-safe-path-multifile | yes | yes | 0 |
| 18-pagination-multifile | yes | yes | 0 |

This score measures the repository's narrow deterministic task patterns. It does not replace the paired model benchmark in `RESULTS.md`, which must run against an available local model endpoint.
