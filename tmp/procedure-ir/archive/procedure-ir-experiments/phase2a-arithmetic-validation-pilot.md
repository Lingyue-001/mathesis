# Phase 2A-3 Arithmetic Validation Pilot

- executed_results: 8
- all_pass: true

## Results

- Proc.2.3.step.1 | 24 * 2392 = 57408 | expected={"product":57408} | computed={"product":57408} | pass=true
- Proc.2.3.step.2 | floor(57408 / 81) = 708 | expected={"accumulated_days":708} | computed={"accumulated_days":708} | pass=true
- Proc.2.3.step.2 | 57408 mod 81 = 60 | expected={"lesser_remainder":60} | computed={"lesser_remainder":60} | pass=true
- Proc.2.3.step.4 | 708 mod 60 = 48 | expected={"greater_remainder":48} | computed={"greater_remainder":48} | pass=true
- Proc.2.3.step.6 | 2392 = 29 * 81 + 43 | expected={"quotient":29,"remainder":43} | computed={"quotient":29,"remainder":43} | pass=true
- Proc.2.3.step.8 | 2392 / 4 = 598 | expected={"quarter_factor":598} | computed={"quarter_factor":598} | pass=true
- Proc.2.3.step.8 | 598 = 7 * 81 + 31 | expected={"quotient":7,"remainder":31} | computed={"quotient":7,"remainder":31} | pass=true
- Proc.2.9.step.1 | 19 * 81 = 1539 | expected={"concordance_factor":1539} | computed={"concordance_factor":1539} | pass=true

## Excluded From Auto-Run

- Proc.2.3.step.3 | needs_cullen_page_check: current allowed inputs do not fully reconcile source threshold 38 with Cullen's 43/carry explanation, so keep out of arithmetic validation.
- Proc.2.3.step.5 | Counting-outside convention is explicitly excluded from run-now arithmetic validation.
- Proc.2.3.step.7 | Candidate but not run now: arithmetic core is partly formalized, but this round keeps it outside auto-run.
- Proc.2.3.step.9 | Only C-level translation backup is present, so this step must be downgraded from clean formalizable_now and excluded from run-now validation.
- Proc.2.4.step.1 | Although the multiplication itself is clear, Proc. 2.4 remains under a source/Cullen discrepancy and is not admitted to the run-now whitelist in this round.
- Proc.2.4.step.2a | Source/Cullen discrepancy blocks deterministic arithmetic formalization.
- Proc.2.4.step.2b | Worked-example arithmetic exists, but this round keeps all Proc. 2.4 steps out of run-now because the discrepancy and off-by-one naming risk remain open.
- Proc.2.4.step.3 | Counting-outside convention is excluded from arithmetic auto-run.
- Proc.2.4.step.4 | Calendrical placement logic still requires human review and discrepancy resolution.
- Proc.2.5.step.1 | Candidate but not run now: arithmetic core is partly formalized, but this round keeps it outside auto-run.
- Proc.2.5.step.2 | Candidate but not run now: arithmetic core is partly formalized, but this round keeps it outside auto-run.
- Proc.2.5.step.3 | As instructed, 如法 counting remains excluded from run-now arithmetic validation.
- Proc.2.9.step.2 | Candidate but not run now: arithmetic core is partly formalized, but this round keeps it outside auto-run.
- Proc.2.9.step.3 | Borrow bookkeeping is explicitly excluded from run-now arithmetic validation.
- Proc.3.2.step.1 | Proc. 3.2 is benchmark only and must not be promoted into the Santong run-now whitelist.
- Proc.3.2.step.2 | Proc. 3.2 is benchmark only and must not be promoted into the Santong run-now whitelist.
- Proc.3.2.step.3 | Proc. 3.2 remains benchmark only; C-level backup also blocks auto-run.
- Proc.3.2.step.4 | Benchmark-only table/counting convention remains human review.
- Proc.3.2.step.5 | Benchmark-only table/counting convention remains human review.
- Proc.3.2.step.6 | Benchmark-only labeling/counting convention remains human review.
