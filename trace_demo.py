"""Run actual verification demos with a privately entered Neatlogs project key."""
import getpass
import json
import os
from pathlib import Path


def main():
    key = os.getenv('NEATLOGS_API_KEY') or getpass.getpass('Paste your Neatlogs project API key (hidden): ')
    if not key.strip():
        raise SystemExit('A project key is required. No trace was sent.')
    os.environ['NEATLOGS_API_KEY'] = key.strip()
    try:
        import neatlogs
    except ImportError:
        raise SystemExit('Install the SDK first: python -m pip install neatlogs')
    neatlogs.init(api_key=key.strip(), endpoint='https://ingest.neatlogs.com',
                  workflow_name='repair-verification-demo')
    # Imports after initialization so instrumented functions bind to the active SDK.
    from verified_workflow import verify_candidates
    root = Path(__file__).resolve().parent
    fixture = root / 'fixtures/buggy_calculator'
    try:
        with neatlogs.trace('incorrect-repair-rejected', kind='WORKFLOW'):
            before = verify_candidates(fixture, ['subtotal'], root / 'artifacts/live-rejected.json')
        with neatlogs.trace('candidate-retry-verified', kind='WORKFLOW'):
            after = verify_candidates(fixture, ['subtotal', 'subtotal - discount'],
                                      root / 'artifacts/live-verified.json')
        print(json.dumps({'before': before['verdict'], 'after': after['verdict'],
                          'tests_unchanged': all(a.get('tests_unchanged', False)
                                                 for a in after['attempts'])}, indent=2))
        print('Check both workflow traces in the dashboard. Export success alone is not proof of ingestion.')
    finally:
        neatlogs.flush(timeout_millis=10000)
        neatlogs.shutdown(timeout_millis=10000)


if __name__ == '__main__':
    main()
