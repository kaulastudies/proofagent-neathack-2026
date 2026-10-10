"""Feedback-driven repairs with independent verification and atomic resume state.

Only bundled trusted fixtures may execute. Proposal syntax is restricted to
arithmetic. State binds fixture bytes, planner identity and retry budget.
"""
import argparse
import difflib
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from repair_agent import run_tests, trace, neatlogs
from verified_workflow import validate_expression
from model_planner import GeminiPlanner, ReplayPlanner

ROOT = Path(__file__).resolve().parent
CASES = {
 'discount': {'folder': 'buggy_calculator', 'needle': '(subtotal - discount) - discount',
              'variables': ['subtotal', 'discount'], 'replay': ['subtotal', 'subtotal - discount'],
              'requirement': 'Apply the discount exactly once to the sum of prices.'},
 'tax': {'folder': 'tax_order', 'needle': 'subtotal * (1 + tax_rate) - discount',
         'variables': ['subtotal', 'discount', 'tax_rate'],
         'replay': ['subtotal - discount', '(subtotal - discount) * (1 + tax_rate)'],
         'requirement': 'Apply the discount before computing tax on the remaining subtotal.'},
 'shipping': {'folder': 'shipping', 'needle': '(subtotal + shipping) - discount * 2',
              'variables': ['subtotal', 'discount', 'shipping'],
              'replay': ['subtotal - discount', 'subtotal - discount + shipping'],
              'requirement': 'Apply discount once to subtotal; add shipping without discounting it.'},
}

def snapshot(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*.py'))}

def save_atomic(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)

class InterruptedRun(RuntimeError):
    pass

@trace('AGENT', 'feedback_driven_repair')
def run(case, planner, state_path, max_attempts=3, stop_after=None):
    if case not in CASES or not 1 <= max_attempts <= 3:
        raise ValueError('Use a registered case and 1–3 attempts')
    config = CASES[case]
    fixture = ROOT / 'fixtures' / config['folder']
    hashes = snapshot(fixture)
    source = (fixture / 'calculator.py').read_text(encoding='utf-8')
    if source.count(config['needle']) != 1:
        raise ValueError('Ambiguous repair location')
    state_path = Path(state_path)
    binding = {'case': case, 'fixture_sha256': hashes,
               'planner': planner.identity, 'max_attempts': max_attempts}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding='utf-8'))
        if state.get('binding') != binding or state.get('schema_version') != 1:
            raise ValueError('Resume refused: fixture, planner, budget or schema changed')
        if state['verdict'] in {'VERIFIED_PASS', 'VERIFIED_FAIL', 'ALREADY_PASSING'}:
            return state
        if state['verdict'] != 'RUNNING' or len(state['attempts']) > max_attempts:
            raise ValueError('Invalid resume state')
    else:
        with tempfile.TemporaryDirectory(prefix='proof-baseline-') as tmp:
            folder = Path(tmp) / 'fixture'
            shutil.copytree(fixture, folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            baseline = run_tests(folder)
        state = {'schema_version': 1, 'binding': binding, 'verdict': 'RUNNING',
                 'baseline': baseline, 'attempts': [], 'events': ['baseline_recorded']}
        if baseline['timed_out']:
            state['verdict'] = 'VERIFIED_FAIL'
            state['failure_reason'] = 'Baseline infrastructure timeout; defect not established'
        elif baseline['passed']:
            state['verdict'] = 'ALREADY_PASSING'
        save_atomic(state_path, state)
        if state['verdict'] != 'RUNNING':
            return state
    while len(state['attempts']) < max_attempts:
        if snapshot(fixture) != hashes:
            raise ValueError('Fixture changed during run')
        context = {'case': case, 'requirement': config['requirement'], 'source': source,
                   'allowed_variables': config['variables'], 'baseline': state['baseline'],
                   'attempts': state['attempts']}
        # A provider failure preserves state; resume does not replay verified attempts.
        proposal = planner.propose(context)
        attempt = {'number': len(state['attempts']) + 1, 'proposal': proposal}
        expression = proposal.get('expression')
        try:
            validate_expression(expression, set(config['variables']))
        except (ValueError, SyntaxError, TypeError) as exc:
            attempt.update(status='REJECTED', reason=str(exc))
        else:
            candidate = source.replace(config['needle'], expression, 1)
            with tempfile.TemporaryDirectory(prefix='proof-candidate-') as tmp:
                folder = Path(tmp) / 'fixture'
                shutil.copytree(fixture, folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                (folder / 'calculator.py').write_text(candidate, encoding='utf-8', newline='')
                verification = run_tests(folder)
                observed = snapshot(folder)
            expected = dict(hashes)
            expected['calculator.py'] = hashlib.sha256(candidate.encode()).hexdigest()
            attempt.update(verification=verification, files_unchanged_except_patch=observed == expected,
                source_after_sha256=expected['calculator.py'],
                patch=''.join(difflib.unified_diff(source.splitlines(True), candidate.splitlines(True),
                            fromfile='a/calculator.py', tofile='b/calculator.py')))
            passed = verification['passed'] and observed == expected and snapshot(fixture) == hashes
            attempt['status'] = 'VERIFIED_PASS' if passed else 'VERIFIED_FAIL'
        state['attempts'].append(attempt)
        state['events'].append('attempt_' + str(attempt['number']) + '_' + attempt['status'])
        if attempt['status'] == 'VERIFIED_PASS':
            state['verdict'] = 'VERIFIED_PASS'
            state['accepted_expression'] = expression
        elif len(state['attempts']) >= max_attempts:
            state['verdict'] = 'VERIFIED_FAIL'
        state['original_unchanged'] = snapshot(fixture) == hashes
        save_atomic(state_path, state)
        if state['verdict'] != 'RUNNING':
            break
        if stop_after is not None and len(state['attempts']) >= stop_after:
            raise InterruptedRun('Checkpoint saved; rerun the same command without --stop-after to resume')
    return state

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=CASES, default='tax')
    parser.add_argument('--mode', choices=['live', 'replay'], required=True)
    parser.add_argument('--model', default='gemini-3.8-flash')
    parser.add_argument('--state', type=Path)
    parser.add_argument('--stop-after', type=int)
    parser.add_argument('--traces', action='store_true')
    args = parser.parse_args()
    if args.traces:
        if not neatlogs or not os.getenv('NEATLOGS_API_KEY'):
            parser.error('--traces requires neatlogs and NEATLOGS_API_KEY')
        options = {'instrumentations': ['google_genai']} if args.mode == 'live' else {}
        neatlogs.init(workflow_name='proofagent-' + args.mode, **options)
    try:
        planner = GeminiPlanner(args.model) if args.mode == 'live' else ReplayPlanner(CASES[args.case]['replay'])
        result = run(args.case, planner, args.state or Path('artifacts') / (args.mode + '-' + args.case + '.json'),
                     stop_after=args.stop_after)
        print(json.dumps(result, indent=2))
        return 0 if result['verdict'] in {'VERIFIED_PASS', 'ALREADY_PASSING'} else 1
    except InterruptedRun as exc:
        print(str(exc))
        return 75
    except Exception as exc:
        # Provider exceptions may contain secrets/URLs; don't echo their text.
        print('Run stopped:', type(exc).__name__, 'Check credentials, dependencies, and checkpoint compatibility.')
        return 2
    finally:
        if args.traces:
            neatlogs.flush(timeout_millis=10000)
            neatlogs.shutdown(timeout_millis=10000)

if __name__ == '__main__':
    raise SystemExit(main())
