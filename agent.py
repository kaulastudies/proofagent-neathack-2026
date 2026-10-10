"""ProofAgent hackathon prototype: evidence-driven tool recovery and verification."""
import argparse
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    import neatlogs
except ImportError:
    neatlogs = None


def trace(kind, name):
    def decorate(fn):
        if neatlogs is not None:
            return neatlogs.span(kind=kind, name=name)(fn)
        return fn
    return decorate


@dataclass
class RunState:
    case: str
    attempts: int = 0
    events: list = field(default_factory=list)
    verdict: str = "UNVERIFIED"
    artifact: dict = field(default_factory=dict)


CASES = {
    "transient_failure": {"payload": [2, 4, 6], "expected": 12, "fail_once": True},
    "incorrect_output": {"payload": [2, 4, 6], "expected": 13, "fail_once": False},
    "success": {"payload": [3, 5, 7], "expected": 15, "fail_once": False},
}


@trace("TOOL", "compute_sum")
def compute_sum(payload, attempt, fail_once):
    if fail_once and attempt == 1:
        raise TimeoutError("simulated transient tool timeout")
    return sum(payload)


@trace("TOOL", "independent_verifier")
def verify(payload, candidate, expected):
    independent_result = sum(payload)
    return {
        "matches_independent_oracle": candidate == independent_result,
        "matches_acceptance_spec": candidate == expected,
        "independent_result": independent_result,
    }


@trace("AGENT", "proofagent_execute")
def execute(case, max_attempts=2):
    if case not in CASES:
        raise ValueError(f"Unknown case: {case}")
    cfg = CASES[case]
    state = RunState(case)
    for attempt in range(1, max_attempts + 1):
        state.attempts = attempt
        state.events.append({"step": "plan", "attempt": attempt, "action": "compute_and_verify"})
        try:
            candidate = compute_sum(cfg["payload"], attempt, cfg["fail_once"])
        except TimeoutError as exc:
            state.events.append({"step": "tool_error", "attempt": attempt, "type": "TimeoutError", "reason": str(exc)})
            if attempt < max_attempts:
                state.events.append({"step": "recover", "action": "retry_transient_tool_failure"})
                continue
            state.verdict = "VERIFIED_FAIL"
            break
        check = verify(cfg["payload"], candidate, cfg["expected"])
        state.artifact = {"candidate": candidate, "expected": cfg["expected"], "checks": check}
        state.events.append({"step": "verify", "attempt": attempt, "checks": check})
        if check["matches_independent_oracle"] and check["matches_acceptance_spec"]:
            state.verdict = "VERIFIED_PASS"
        else:
            # Do not tune the oracle or acceptance requirement merely to achieve PASS.
            state.verdict = "VERIFIED_FAIL"
            state.events.append({"step": "stop", "reason": "deterministic_acceptance_failure"})
        break
    return asdict(state)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, default="transient_failure")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if neatlogs is not None:
        neatlogs.init(api_key=os.getenv("NEATLOGS_API_KEY"), workflow_name="proofagent-neathack")
    try:
        result = execute(args.case)
        rendered = json.dumps(result, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
    finally:
        if neatlogs is not None:
            neatlogs.flush()
            neatlogs.shutdown()


if __name__ == "__main__":
    main()
