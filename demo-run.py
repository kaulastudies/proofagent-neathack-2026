"""Credential-free demonstration; every proposal is explicitly offline replay."""
import json
import tempfile
from pathlib import Path
from model_planner import ReplayPlanner
from resumable_agent import CASES, InterruptedRun, run

with tempfile.TemporaryDirectory(prefix='proofagent-demo-') as temp:
    folder = Path(temp)
    print('PROOFAGENT | OFFLINE REPLAY | REAL INDEPENDENT TEST EXECUTION')
    summary = []
    for case, config in CASES.items():
        result = run(case, ReplayPlanner(config['replay']), folder / (case + '.json'))
        item = {'case': case, 'baseline_passed': result['baseline']['passed'],
                'attempts': [a['status'] for a in result['attempts']],
                'verdict': result['verdict'], 'original_unchanged': result['original_unchanged']}
        print(json.dumps(item))
        summary.append(item)
    state = folder / 'resume.json'
    try:
        run('tax', ReplayPlanner(CASES['tax']['replay']), state, stop_after=1)
    except InterruptedRun:
        print('INTERRUPTED after failed candidate; checkpoint saved')
    result = run('tax', ReplayPlanner(CASES['tax']['replay']), state)
    print('RESUMED:', result['verdict'], '| persisted attempts:', len(result['attempts']))
    target = Path('artifacts/demo-summary.json')
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({'mode':'offline-replay','cases':summary,
        'resume_verdict':result['verdict']}, indent=2) + '\n')
