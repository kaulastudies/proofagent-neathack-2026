# Entire Graph integration evidence

Captured October 12, 2026, while improving ProofAgent checkpoint verification.

- Entire CLI: 0.11.4 (official release archive; SHA-256 verified against official checksums).
- Entire Graph: v0.4.0, installed through `entire plugin install graph`.
- `doctor.json`: vendor-reported local/no-egress behavior.
- `resume-query-before.json`: actual Graph search output against the event repository before the repair.
- `resume-impact-before.json`: actual impact analysis for `resumable_agent.run`; identified the CLI, demonstration and regression tests as callers.
- `resume-query-after.json`: actual Graph search after extracting reusable independent proposal verification and adding completed-checkpoint revalidation.
- `pre-edit-baseline.json`: Graph verification baseline, exit 1. Executed the newly added regression tests against the prior committed implementation in a separate temporary clone.
- `verification.txt`: Graph adjudication after repair, exit 0. Graph v0.4.0 does not parse unittest test IDs; this is explicitly an **exit-code-only verdict**, not a per-test comparison.

Reproduce with the official CLI and Graph plugin:

```sh
entire graph search --repo . --query 'checkpoint resume trusts saved verified pass without rerunning independent acceptance tests' --format json --top-k 5
entire graph impact --repo . --symbol run --file resumable_agent.py --format json
python -m unittest discover -s tests -v
```

These files demonstrate actual Entire Graph use during development. They are not an Entire session checkpoint. Static relations are heuristic; the repair was verified using real subprocess acceptance tests.

The earlier script-specific candidate reports remain historical offline evidence. The new schema v2 binds verifier source and case specification; v1 state cannot be resumed under v2.
