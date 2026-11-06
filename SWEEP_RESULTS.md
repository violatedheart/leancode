# LeanCode feature ablation sweep

Model: `qwen2.5-coder:7b-instruct-q4_K_M`. Each lane runs the same tasks and budget; hidden tests are injected only after an agent run.

| Feature set | Pass rate | Total tokens | Tokens per solved task | Time (s) |
|---|---:|---:|---:|---:|
| all-on | 6/18 (33.3%) | 33909 | 5651.5 | 270.0 |
| without-reproduce | 8/18 (44.4%) | 30747 | 3843.4 | 299.9 |
| without-hypothesize | 5/18 (27.8%) | 37476 | 7495.2 | 355.2 |
| without-best-of-three | 6/18 (33.3%) | 39147 | 6524.5 | 330.8 |
| without-playbook | 6/18 (33.3%) | 34687 | 5781.2 | 285.5 |
| without-notes | 6/18 (33.3%) | 34013 | 5668.8 | 336.8 |

Keep a feature enabled by default only when the all-on lane improves pass rate or tokens per solved task over the lane with that feature ablated.

## Run status

- all-on: 02-palindrome-normalize: hidden tests failed: 
======================================================================
FAIL: test_unicode_and_empty (test_hidden.HiddenPalindromeTests.test_unicode_and_empty)
--------------------; 07-parse-bool: hidden tests failed: 
======================================================================
ERROR: test_zero_one_and_invalid (test_hidden.HiddenBoolTests.test_zero_one_and_invalid)
-------------------; 09-invoice-tax-multifile: hidden tests failed: 
======================================================================
FAIL: test_discount_applies_before_tax (test_solution.TestInvoice.test_discount_applies_before_tax)
--------; 13-env-port-multifile: hidden tests failed: 
======================================================================
ERROR: test_blank_defaults_and_invalid_range_rejected (test_hidden.PortTests.test_blank_defaults_and_invalid
- without-reproduce: 02-palindrome-normalize: hidden tests failed: 
======================================================================
FAIL: test_unicode_and_empty (test_hidden.HiddenPalindromeTests.test_unicode_and_empty)
--------------------; 07-parse-bool: hidden tests failed: 
======================================================================
ERROR: test_zero_one_and_invalid (test_hidden.HiddenBoolTests.test_zero_one_and_invalid)
-------------------; 09-invoice-tax-multifile: hidden tests failed: 
======================================================================
FAIL: test_discount_applies_before_tax (test_solution.TestInvoice.test_discount_applies_before_tax)
--------; 13-env-port-multifile: hidden tests failed: 
======================================================================
ERROR: test_blank_defaults_and_invalid_range_rejected (test_hidden.PortTests.test_blank_defaults_and_invalid
- without-hypothesize: 02-palindrome-normalize: hidden tests failed: 
======================================================================
FAIL: test_unicode_and_empty (test_hidden.HiddenPalindromeTests.test_unicode_and_empty)
--------------------; 07-parse-bool: hidden tests failed: 
======================================================================
ERROR: test_zero_one_and_invalid (test_hidden.HiddenBoolTests.test_zero_one_and_invalid)
-------------------; 09-invoice-tax-multifile: hidden tests failed: 
======================================================================
FAIL: test_unknown_country_and_rounding (test_hidden.HiddenInvoiceTests.test_unknown_country_and_rounding)
-; 13-env-port-multifile: hidden tests failed: 
======================================================================
ERROR: test_blank_defaults_and_invalid_range_rejected (test_hidden.PortTests.test_blank_defaults_and_invalid
- without-best-of-three: 02-palindrome-normalize: hidden tests failed: 
======================================================================
FAIL: test_unicode_and_empty (test_hidden.HiddenPalindromeTests.test_unicode_and_empty)
--------------------; 07-parse-bool: hidden tests failed: 
======================================================================
ERROR: test_zero_one_and_invalid (test_hidden.HiddenBoolTests.test_zero_one_and_invalid)
-------------------; 09-invoice-tax-multifile: hidden tests failed: 
======================================================================
FAIL: test_unknown_country_and_rounding (test_hidden.HiddenInvoiceTests.test_unknown_country_and_rounding)
-; 13-env-port-multifile: hidden tests failed: 
======================================================================
ERROR: test_blank_defaults_and_invalid_range_rejected (test_hidden.PortTests.test_blank_defaults_and_invalid
- without-playbook: 02-palindrome-normalize: hidden tests failed: 
======================================================================
FAIL: test_unicode_and_empty (test_hidden.HiddenPalindromeTests.test_unicode_and_empty)
--------------------; 07-parse-bool: hidden tests failed: 
======================================================================
ERROR: test_zero_one_and_invalid (test_hidden.HiddenBoolTests.test_zero_one_and_invalid)
-------------------; 09-invoice-tax-multifile: hidden tests failed: 
======================================================================
FAIL: test_discount_applies_before_tax (test_solution.TestInvoice.test_discount_applies_before_tax)
--------; 13-env-port-multifile: hidden tests failed: 
======================================================================
ERROR: test_blank_defaults_and_invalid_range_rejected (test_hidden.PortTests.test_blank_defaults_and_invalid
- without-notes: 02-palindrome-normalize: hidden tests failed: 
======================================================================
FAIL: test_unicode_and_empty (test_hidden.HiddenPalindromeTests.test_unicode_and_empty)
--------------------; 07-parse-bool: hidden tests failed: 
======================================================================
ERROR: test_zero_one_and_invalid (test_hidden.HiddenBoolTests.test_zero_one_and_invalid)
-------------------; 09-invoice-tax-multifile: hidden tests failed: 
======================================================================
FAIL: test_discount_applies_before_tax (test_solution.TestInvoice.test_discount_applies_before_tax)
--------; 13-env-port-multifile: hidden tests failed: 
======================================================================
ERROR: test_blank_defaults_and_invalid_range_rejected (test_hidden.PortTests.test_blank_defaults_and_invalid
