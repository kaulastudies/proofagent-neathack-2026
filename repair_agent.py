"""Restricted, evidence-driven repo repair agent for a reproducible Python defect.

Safety: operates only on copied local fixtures; never executes model-generated shell commands.
The registered repair operations are narrowly scoped and independently tested.
"""
import argparse
import ast
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import neatlogs
except ImportError:
    neatlogs = None


def trace(kind, name, capture_input=True):
    def wrap(fn):
        return neatlogs.span(kind=kind, name=name, capture_input=capture_input)(fn) if neatlogs else fn
    return wrap


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@trace('TOOL', 'run_independent_tests')
def run_tests(workdir, timeout=15):
    try:
        proc = subprocess.run(
            [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
            cwd=workdir, capture_output=True, text=True, timeout=timeout,
            env={**{k: os.environ[k] for k in ('PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP') if k in os.environ},
                 'PYTHONPATH': '', 'PYTHONDONTWRITEBYTECODE': '1'},
        )
        return {'passed': proc.returncode == 0, 'exit_code': proc.returncode,
                'output': (proc.stdout + proc.stderr)[-5000:], 'timed_out': False}
    except subprocess.TimeoutExpired:
        return {'passed': False, 'exit_code': None, 'output': 'Test timeout', 'timed_out': True}


@trace('TOOL', 'diagnose_python_ast')
def diagnose(source):
    """Recognize a specific error signature, without trusting the failure text alone."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'calculate_total':
            for child in ast.walk(node):
                if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Sub):
                    if isinstance(child.left, ast.Name) and child.left.id == 'subtotal' and isinstance(child.right, ast.Name) and child.right.id == 'discount':
                        return 'discount_subtraction'
    return None


@trace('TOOL', 'apply_scoped_patch')
def apply_patch(source, diagnosis):
    if diagnosis != 'discount_subtraction':
        raise ValueError('No supported repair')
    # AST pins the exact defect; patching is limited to this one arithmetic operator.
    needle = '(subtotal - discount) - discount'
    if source.count(needle) != 1:
        raise ValueError('Ambiguous patch location')
    return source.replace(needle, 'subtotal - discount', 1)


@trace('AGENT', 'repair_repo')
def repair_repo(fixture, destination, max_attempts=2, simulate_timeout=False):
    fixture, destination = Path(fixture).resolve(), Path(destination).resolve()
    if destination == fixture or fixture in destination.parents or destination in fixture.parents:
        raise ValueError('Fixture and destination must be separate')
    if not (fixture / 'calculator.py').is_file() or not (fixture / 'tests' / 'test_calculator.py').is_file():
        raise ValueError('Expected fixture layout absent')
    if destination.exists():
        raise FileExistsError('Destination must not exist: ' + str(destination))
    shutil.copytree(fixture, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
    path = destination / 'calculator.py'
    original = path.read_text(encoding='utf-8')
    events = []
    before_hash = checksum(path)
    baseline = run_tests(destination)
    events.append({'action': 'run_baseline', 'passed': baseline['passed'], 'exit_code': baseline['exit_code']})
    if baseline['passed']:
        return {'verdict': 'ALREADY_PASSING', 'events': events, 'baseline': baseline, 'after': baseline, 'patch': '', 'before_sha256': before_hash, 'after_sha256': before_hash}
    for attempt in range(1, max_attempts + 1):
        events.append({'action': 'inspect', 'attempt': attempt})
        if simulate_timeout and attempt == 1:
            events.append({'action': 'tool_timeout', 'attempt': attempt})
            if attempt < max_attempts:
                events.append({'action': 'recover_retry', 'attempt': attempt})
                continue
            break
        diagnosis = diagnose(original)
        events.append({'action': 'diagnose', 'signature': diagnosis})
        if not diagnosis:
            break
        candidate = apply_patch(original, diagnosis)
        path.write_text(candidate, encoding='utf-8')
        events.append({'action': 'patch', 'attempt': attempt})
        after = run_tests(destination)
        events.append({'action': 'verify', 'passed': after['passed'], 'exit_code': after['exit_code']})
        if after['passed']:
            diff = ''.join(difflib.unified_diff(original.splitlines(keepends=True), candidate.splitlines(keepends=True), fromfile='a/calculator.py', tofile='b/calculator.py'))
            return {'verdict': 'VERIFIED_PASS', 'events': events, 'baseline': baseline, 'after': after, 'patch': diff, 'before_sha256': before_hash, 'after_sha256': checksum(path)}
        # Never weaken tests. Return the attempted change to the original state.
        path.write_text(original, encoding='utf-8')
        events.append({'action': 'rollback', 'reason': 'independent_tests_failed'})
        break
    return {'verdict': 'VERIFIED_FAIL', 'events': events, 'baseline': baseline, 'after': run_tests(destination), 'patch': '', 'before_sha256': before_hash, 'after_sha256': checksum(path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', default=str(Path(__file__).parent / 'fixtures' / 'buggy_calculator'))
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--simulate-timeout', action='store_true')
    args = parser.parse_args()
    if neatlogs:
        neatlogs.init(api_key=os.getenv('NEATLOGS_API_KEY'), workflow_name='proofagent-repo-repair')
    try:
        if args.destination:
            result = repair_repo(args.fixture, args.destination, simulate_timeout=args.simulate_timeout)
        else:
            with tempfile.TemporaryDirectory(prefix='proofagent-') as temp:
                result = repair_repo(args.fixture, Path(temp) / 'candidate', simulate_timeout=args.simulate_timeout)
        payload = json.dumps(result, indent=2) + '\n'
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding='utf-8')
        print(payload)
    finally:
        if neatlogs:
            neatlogs.flush()
            neatlogs.shutdown()


if __name__ == '__main__':
    main()
