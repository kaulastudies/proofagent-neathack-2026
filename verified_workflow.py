"""Evaluate repair proposals on trusted local fixtures using frozen acceptance tests.

This runner is not a sandbox for arbitrary repositories. Candidates are data-only
arithmetic expressions; it does not execute generated commands or general code.
"""
import ast
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from repair_agent import run_tests, trace, neatlogs
import os


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_expression(expression, variables=None):
    if not isinstance(expression, str) or len(expression) > 240:
        raise ValueError('Candidate must be a short arithmetic expression')
    node = ast.parse(expression, mode='eval')
    allowed = (ast.Expression, ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div,
               ast.Name, ast.Load, ast.Constant)
    for item in ast.walk(node):
        if not isinstance(item, allowed):
            raise ValueError('Candidate contains unsupported syntax')
        if isinstance(item, ast.Name) and item.id not in (variables or {'subtotal', 'discount'}):
            raise ValueError('Candidate uses an unknown variable')
        if isinstance(item, ast.Constant) and type(item.value) not in (int, float):
            raise ValueError('Candidate contains a nonnumeric literal')
    return expression


@trace('AGENT', 'verify_repair_candidates')
def verify_candidates(fixture, candidates, output):
    fixture = Path(fixture).resolve()
    source = fixture / 'calculator.py'
    tests = fixture / 'tests'
    frozen = {str(p.relative_to(tests)): digest(p) for p in tests.rglob('*.py')}
    if not frozen:
        raise ValueError('Independent acceptance tests are required')
    original = source.read_text(encoding='utf-8')
    needle = '(subtotal - discount) - discount'
    if original.count(needle) != 1:
        raise ValueError('Unsupported fixture; expected one repair location')
    report = {'schema_version': 1, 'verdict': 'VERIFIED_FAIL',
              'planner': 'supplied_candidates', 'tests_sha256': frozen,
              'source_before_sha256': digest(source), 'attempts': []}
    with tempfile.TemporaryDirectory(prefix='proofagent-verify-') as tmp:
        baseline_dir = Path(tmp) / 'baseline'
        shutil.copytree(fixture, baseline_dir)
        report['baseline'] = run_tests(baseline_dir)
        if report['baseline']['passed']:
            report['verdict'] = 'ALREADY_PASSING'
        else:
            for index, expression in enumerate(candidates[:3], 1):
                attempt = {'number': index, 'expression': expression}
                report['attempts'].append(attempt)
                try:
                    validate_expression(expression)
                except (ValueError, SyntaxError) as exc:
                    attempt.update(status='REJECTED', reason=str(exc))
                    continue
                candidate_dir = Path(tmp) / ('candidate-' + str(index))
                shutil.copytree(fixture, candidate_dir)
                patched = candidate_dir / 'calculator.py'
                patched.write_text(original.replace(needle, expression, 1), encoding='utf-8')
                attempt['verification'] = run_tests(candidate_dir)
                observed = {str(p.relative_to(candidate_dir / 'tests')): digest(p)
                            for p in (candidate_dir / 'tests').rglob('*.py')}
                attempt['tests_unchanged'] = observed == frozen
                attempt['source_after_sha256'] = digest(patched)
                passed = attempt['verification']['passed'] and attempt['tests_unchanged']
                attempt['status'] = 'VERIFIED_PASS' if passed else 'VERIFIED_FAIL'
                if passed:
                    report['verdict'] = 'VERIFIED_PASS'
                    report['accepted_expression'] = expression
                    break
    report['original_unchanged'] = digest(source) == report['source_before_sha256']
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', default=str(Path(__file__).parent / 'fixtures/buggy_calculator'))
    parser.add_argument('--candidates', default='["subtotal", "subtotal - discount"]')
    parser.add_argument('--output', default='artifacts/candidate-verification.json')
    args = parser.parse_args()
    candidates = json.loads(args.candidates)
    if not isinstance(candidates, list) or not all(isinstance(c, str) for c in candidates):
        parser.error('candidates must be a JSON array of expressions')
    if neatlogs and os.getenv('NEATLOGS_API_KEY'):
        neatlogs.init(api_key=os.environ['NEATLOGS_API_KEY'], workflow_name='proofagent-candidate-verification')
    try:
        print(json.dumps(verify_candidates(args.fixture, candidates, args.output), indent=2))
    finally:
        if neatlogs and os.getenv('NEATLOGS_API_KEY'):
            neatlogs.flush()
            neatlogs.shutdown()
