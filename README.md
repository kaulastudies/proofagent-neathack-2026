# ProofAgent — neatHack 2026

**An agent's repair is a proposal. Success needs independent evidence.**

Team: **AI Evaluation Lab**. Event code lives here; the pre-existing AI Evaluation Lab repository remains separate.

**[Watch the 2:21 demo](artifacts/ProofAgent_neatHack_demo.mp4)** · [Live verification report](artifacts/neatlogs/live-tax-verified.json) · [cfo.ai business plan](docs/cfo/ProofAgent_Business_Plan_Updated.pdf)

The demo is a silent, captioned walkthrough of actual artifacts, rather than an interactive screen recording. It distinguishes the real Claude run from scripted recovery tests.

ProofAgent repairs arithmetic defects in three trusted billing fixtures. It runs the failing baseline, asks a planner for a restricted arithmetic expression, applies the proposal in a temporary copy, and checks unchanged acceptance tests. Failed proposals feed back to the planner. A verified attempt is saved atomically so another process can resume without repeating earlier attempts.

## What works

- Discount, tax-order and shipping defect cases, with real Python subprocess tests.
- A bounded three-attempt loop, restricted expression grammar, immutable fixture hashes and patch diffs.
- Actual process interruption and recovery from a saved checkpoint.
- Offline replay mode for reproducible evidence, explicitly labeled as scripted.
- Gemini structured-output planner implemented; live execution awaits an API key and validation.
- Neatlogs ingestion for the earlier candidate-verification demo was observed on October 10: one rejected repair and one verified recovery. The actual Claude Haiku tax-repair trace was also observed after the gateway formatting fix; see `artifacts/neatlogs/`.
- 27 regression tests pass locally. GitHub Actions checks Linux and Windows.

Run `python demo-run.py` for a compact credential-free demonstration of all three cases and checkpoint recovery. All proposals in this demo are scripted offline replay; tests execute normally.

## Run without credentials

Python 3.10+; no dependencies required for offline runs.

```sh
python -m unittest discover -s tests -v
python resumable_agent.py --mode replay --case tax --state artifacts/my-tax-run.json
```

Interrupt then resume in a **new process** (first command intentionally exits 75):

```sh
python resumable_agent.py --mode replay --case shipping --state artifacts/resume-demo.json --stop-after 1
python resumable_agent.py --mode replay --case shipping --state artifacts/resume-demo.json
```

Use a new state filename for a fresh run. A completed successful checkpoint independently reruns acceptance tests before returning success. Checkpoints are local files, not signed attestations; protect them against manual modification. Changing fixture bytes, verifier source, case specification, planner identity or attempt budget refuses resume. Schema v1 states require a fresh run under v2.

## Free hackathon model gateway

The organizer supplies an OpenAI-compatible LiteLLM endpoint with Nova/Claude model aliases. Use `live_demo.py` (default provider `litellm`, model `claude-haiku`) for the shared team key and actual neatlogs tracing:

```sh
python -m venv .venv
# Windows: use .\.venv\Scripts\python.exe in place of .venv/bin/python
.venv/bin/python -m pip install -r requirements-hackathon.txt
.venv/bin/python live_demo.py --case tax
```

The launcher prompts privately for the LiteLLM key and neatlogs project key; it does not write keys to disk. The gateway adapter limits each response to 384 tokens, disables SDK automatic retries, and accepts plain JSON or one complete JSON fence, and rejects prose, malformed or truncated proposals. The independent acceptance gate decides success. Token counts and latency are saved in candidate evidence when returned by the provider; dollar cost remains unknown unless supported by provider billing evidence. The organizer's shared $20 budget is enforced by the gateway, not this application.

A real Claude Haiku tax repair passed unchanged independent tests on October 12 and its five-span trace was observed in neatlogs. The earlier live call failed JSON parsing; accepting one complete JSON fence fixed that formatting failure without changing acceptance tests. The verified call reported 598 input + 150 output tokens, 748 total, and 9.344 seconds of model latency. See `artifacts/neatlogs/` for the report and screenshots. The earlier scripted candidate-rejection demo and interruption tests remain separately labeled evidence. No replay fallback is substituted for a failed live call.

## Gemini planner (alternative)

Use an isolated environment; do not install into your global Python environment.

```sh
python -m venv .venv
# Windows: .\.venv\Scripts\python.exe
.venv/bin/python -m pip install -r requirements-live.txt
# Configure GEMINI_API_KEY privately in your local shell/secret manager.
.venv/bin/python resumable_agent.py --mode live --case tax --state artifacts/live-tax.json
```

The adapter follows Google's Interactions structured-output API. `--model` selects the model; default `gemini-3.8-flash`. Missing credentials or provider errors stop the run, preserving completed attempts. They do not silently substitute replay results. At most three proposals per fresh run; a provider interruption before saving a proposal may require another request on resume. No financial spending cap is enforced by the application.

## Neatlogs

Set `NEATLOGS_API_KEY` privately and add `--traces` to an agent command. Live mode enables `google_genai` automatic instrumentation. Import/init order is important: the entry point initializes instrumentation before constructing the model client. Always inspect actual ingestion before claiming cloud integration.

The earlier live evidence can be regenerated using `python trace_demo.py`; it privately prompts for the project key. Recorded trace IDs: `bc9c2e5f96c4d63b9e4eb9f1d9ab1b79` (rejected repair), `bab3fd866bebe19ed15c8c06629223c4` (verified second candidate). Account access is required to view the project's traces.

## Scope and limits

This is a bounded repair/evaluation agent on bundled trusted fixtures. It does not repair arbitrary repositories, execute generated shell commands, or provide a sandbox for untrusted Python. Baseline/test subprocesses execute the trusted fixture. Passing these small acceptance suites is evidence for these cases, not proof of general correctness. Retry state is atomic but not concurrency-safe; use one process per state file.

## Submission readiness

- [x] Public event repository and reproducible test evidence
- [x] Neatlogs cloud ingestion observed for candidate-verification demo
- [x] Live Claude Haiku tax repair independently verified and ingested into neatlogs; before/after parser-fix traces in `artifacts/neatlogs/`
- [x] Entire Graph search, impact analysis and verification evidence captured in `artifacts/entire/` (Graph route; no session checkpoint)
- [x] Original cfo.ai business-plan export and independent arithmetic review in `docs/cfo/` and `artifacts/cfo/`
- [x] 2:21 captioned evidence walkthrough covering all three required integrations
- [ ] Team co-participant registration verified separately from GitHub access
- [ ] Official X submission during the announced window

Entire instructions: https://hack.entire.io/neathacks-2026/ and https://github.com/entireio/cli . Install on a machine with a supported authenticated coding agent, enable in this repository, perform genuine agent work and preserve the real checkpoint. No checkpoint is fabricated here.

`docs/cfo/ProofAgent_Business_Plan_Updated.pdf` is the original cfo.ai export. Run `python verify_business_plan.py` to reproduce its arithmetic check. All financial forecasts are hypothetical; opening cash and runway are uncalculated. `business-plan-input.md` is an earlier input sheet, not the export. The starter scripts `agent.py`, `repair_agent.py` and `verified_workflow.py` are retained for reproducibility; their deterministic scenarios must be described accurately.

No credentials belong in this repository.

## Reproduce the video

On Linux with DejaVu fonts, Pillow, Poppler (`pdftoppm`) and FFmpeg installed, run `python render_demo.py`. The renderer uses the committed trace screenshots, live verification report and original cfo.ai export; it makes no model calls. Scene timings are recorded in `artifacts/demo-scenes.json`. Generated frames are excluded from Git.
