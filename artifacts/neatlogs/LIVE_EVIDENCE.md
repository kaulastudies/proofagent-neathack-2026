# Actual model and neatlogs evidence — October 12

Two genuine calls were made to the organizer's LiteLLM endpoint using Claude Haiku. No scripted planner was used for these calls.

## Before

Trace `07d3ad61935978f8d194a239a3708a15` was observed in neatlogs with an Execution Failed detection. It contained three spans, took about 11.4 seconds overall, and the LLM span reported 779 tokens. Claude returned the correct tax expression inside a Markdown JSON fence. The strict bare-JSON parser raised JSONDecodeError; no candidate patch was applied. `live-before.jpg` records the actual trace.

## Change

The gateway adapter now accepts either plain JSON or one complete JSON fence. It does not extract repairs from surrounding prose, accept extra object fields, skip arithmetic validation, or weaken acceptance tests. Two new regressions cover the response-format behavior. Agent input capture is disabled for the orchestration entry point so planner/client objects containing credentials are not serialized into traces.

## After

Trace `d70e80a1d53f145dec4d26dc8d947200` was observed Ready in neatlogs with five spans: agent, baseline tests, Claude Haiku, arithmetic proposal verification, and acceptance tests. The patched copy passed all four tax acceptance tests, with the original fixture unchanged and the acceptance files unchanged. The proposed expression was `(subtotal - discount) * (1 + tax_rate)`.

`live-tax-verified.json` is the actual runtime report. Provider usage: 598 prompt tokens, 150 completion tokens, 748 total; model latency 9344.2 ms. Dollar cost is not claimed because no provider billing measurement was obtained. `live-after.jpg` is the actual ingested trace view.

This before/after proves recovery from an integration formatting failure after a supported code fix. It does not claim that the model initially proposed a mathematically wrong repair. Wrong-candidate rejection and real process interruption/resume are demonstrated separately by the earlier candidate workflow and regression suite.

Project/trace access requires the owner's neatlogs account. Screenshots and the runtime JSON are included so judges can inspect the evidence without that account.
