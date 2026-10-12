"""Prompt for local secrets privately and run genuine model + neatlogs repair.

No replay fallback. No secrets saved to a file. Use your isolated environment.
"""
import argparse
import getpass
import json
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=['discount','tax','shipping'], default='tax')
    parser.add_argument('--state', type=Path)
    parser.add_argument('--provider', choices=['litellm','gemini'], default='litellm')
    parser.add_argument('--model')
    args = parser.parse_args()
    model_key = ('LITELLM_API_KEY','Hackathon LiteLLM key') if args.provider=='litellm' else ('GEMINI_API_KEY','Gemini API key')
    for name, label in [model_key, ('NEATLOGS_API_KEY','Neatlogs project key')]:
        if not os.getenv(name):
            value = getpass.getpass(label + ' (hidden): ').strip()
            if not value:
                raise SystemExit('Live demo requires both keys; no request was made.')
            os.environ[name] = value
    import neatlogs
    neatlogs.init(workflow_name='proofagent-live-demo', instrumentations=['openai' if args.provider=='litellm' else 'google_genai'])
    try:
        from model_planner import GeminiPlanner, LiteLLMPlanner
        from resumable_agent import run
        target = args.state or Path('artifacts') / ('live-demo-' + args.case + '.json')
        planner = LiteLLMPlanner(args.model or 'claude-haiku') if args.provider=='litellm' else GeminiPlanner(args.model or 'gemini-3.8-flash')
        result = run(args.case, planner, target)
        print(json.dumps({'mode':'live-' + args.provider, 'case':args.case, 'verdict':result['verdict'],
            'attempts':len(result['attempts']), 'report':str(target)},indent=2))
        print('Inspect the actual neatlogs trace before claiming ingestion.')
        return 0 if result['verdict'] == 'VERIFIED_PASS' else 1
    except Exception as exc:
        print('Live demo stopped:', type(exc).__name__, '(provider details withheld).')
        return 2
    finally:
        neatlogs.flush(timeout_millis=10000)
        neatlogs.shutdown(timeout_millis=10000)

if __name__ == '__main__':
    raise SystemExit(main())
