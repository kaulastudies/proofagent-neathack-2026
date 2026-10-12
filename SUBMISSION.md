# ProofAgent — submission packet

Submission received on October 12, 2026, confirmed by the organizer's success page supplied by Rama. Submission ID: `745d0a84-9b92-46ca-a8d0-d4af0ac3af7f`. This confirms receipt, not judging results or independent verification of the submitted quote-post.

## Project and team

Project: **ProofAgent**

Team: **AI Evaluation Lab**

Leader: **Rama Chandra** (`kaulastudies`)

Nithya (`nithyaravikumar1518-web`) has verified GitHub write access. Confirm her event check-in before listing her as a registered co-participant; GitHub access alone is not event registration.

## Short description

ProofAgent checks AI-proposed billing repairs against unchanged independent acceptance tests, rejects failing candidates, and resumes after interruption. It preserves the patch, test outcome and checkpoint evidence behind each verdict.

## Problem and solution

An AI-generated patch can look convincing while still producing incorrect results. ProofAgent treats the model's output as a proposal. For three trusted billing fixtures, it runs a failing baseline, requests a restricted arithmetic repair, tests the patched copy independently, and feeds failures back into a bounded attempt loop. The original fixture and acceptance tests are preserved. Successful saved states are re-tested when resumed.

## What is demonstrated

- One actual Claude Haiku tax-repair run passed all four unchanged acceptance tests. It used 748 tokens and took 9.344 seconds at the model call. Dollar cost was not measured.
- A previous actual call failed because the adapter rejected a JSON code fence. Neatlogs showed the failed call and output; the parser was fixed and the live run repeated. This was a developer integration fix, not an autonomous mathematical correction within one run.
- Scripted wrong-proposal rejection and interruption/resume are separate reproducible evidence. The interruption regression exits 75 and resumes in a new process.
- 31 regression tests pass locally; the latest published code CI succeeded on October 12.

## Sponsor use

**neatlogs:** actual model/tool traces, the Execution Failed detection, before/after screenshots and runtime report. On October 12 during final review, the project Incidents page with All / All time showed “No incidents yet.” A published incident or resolution is not claimed. This is a gap against the organizer's additional incident-feature demo guidance.

**Entire:** actual Graph search, impact analysis and verification used to improve completed-checkpoint verification. Outputs are public. Local CLI tracking is enabled for Codex, but hook approval, a genuine session checkpoint and repository mirroring remain incomplete. Final CLI review showed no authenticated account and zero checkpoints. The initialized metadata branch is not a work checkpoint.

**cfo.ai:** original six-month business-plan PDF, with pricing, delivery costs, adoption scenarios, break-even and cash movement. Independent arithmetic reproduction passes. All forecasts are assumptions. No project cash balance was supplied; runway is explicitly uncalculated. Temporary credits are separate from recurring economics.

**Crustdata (optional):** a bounded company-research module is implemented and tested with synthetic responses. Live verification awaits API access. No company results, customers or usage are claimed.

## Links

- Repository: https://github.com/kaulastudies/proofagent-neathack-2026
- Demo (2:21, silent captioned artifact walkthrough): https://github.com/kaulastudies/proofagent-neathack-2026/blob/main/artifacts/ProofAgent_neatHack_demo.mp4
- Live trace evidence: [artifacts/neatlogs/LIVE_EVIDENCE.md](artifacts/neatlogs/LIVE_EVIDENCE.md)
- Entire Graph evidence: [artifacts/entire/PROVENANCE.md](artifacts/entire/PROVENANCE.md)
- Business plan: [original cfo.ai PDF](docs/cfo/ProofAgent_Business_Plan_Updated.pdf)
- Economics verification: [docs/cfo/VERIFY.md](docs/cfo/VERIFY.md)
- CI: https://github.com/kaulastudies/proofagent-neathack-2026/actions/runs/38245911682

## Quote-post draft

Attach the video and quote the official launch post; this text alone is not a submission.

> Our #neatHack submission: ProofAgent — AI Evaluation Lab / Rama Chandra.
>
> An AI patch is a proposal. Independent tests decide whether it works. We verified a live Claude billing repair and tested interruption recovery.
>
> Built with @neatlogs @EntireHQ @arithecfo

Optional first reply with the repository link and evidence details may be prepared separately. Do not claim the optional Crustdata module ran live.

## Demo narration / caption reference

1. Problem: AI patches need evidence beyond their own explanation.
2. Tax fixture: apply the discount before tax; unchanged tests define the expected result.
3. Actual failure: Claude returned correct arithmetic in fenced JSON, and the adapter failed parsing. The trace identifies the error.
4. Fix: accept one complete JSON fence while retaining schema and arithmetic validation. The new live run passes the four acceptance tests.
5. Verification: restricted arithmetic, temporary copies, frozen tests and bounded attempts.
6. Recovery: clearly label scripted candidates; show the real interruption/new-process regression.
7. Entire: explain the actual Graph search, caller impact and before/after verification. Do not show a fabricated checkpoint.
8. cfo.ai: show the original plan and clearly distinguish forecast assumptions from actual traction. Runway remains unknown.
9. Scope and next step: three trusted fixtures; broaden coverage only after more independent evidence.

## Submission procedure and open items

Official launch post: https://x.com/bettersayAJ/status/2109639214723932495

Official form: https://neatlogs.com/submission

Deadline announced in organizer Discord: October 12, 11:55 PM IST. Check Discord for final updates.

- [ ] Resolve or explicitly disclose the incidents-feature evidence gap; no published incident currently exists in the dashboard.
- [ ] Complete/verify Entire mirror, approved hooks and a genuine checkpoint requested in the setup email, or obtain organizer clarification on the existing Graph evidence.
- [ ] Confirm Nithya's event check-in.
- [ ] Publish a public quote of the exact launch post, with the video attached and all three required tags.
- [ ] Copy the actual published quote URL into the submission form; complete the project/team fields and review.
- [x] Submission receipt confirmed from the organizer's success page on October 12, 2026. Reference: `745d0a84-9b92-46ca-a8d0-d4af0ac3af7f`.

The remaining unchecked items are verification follow-ups, not an instruction to submit again. The receipt does not independently establish Nithya's event registration or the contents of the published quote.

## Limits

Bounded prototype, not arbitrary repository repair or an untrusted-code sandbox. Local state is unsigned and intended for one process per state file. Passing the included acceptance suites does not establish general correctness. No customers or revenue are confirmed.
