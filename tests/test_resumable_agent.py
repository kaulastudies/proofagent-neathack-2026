import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from model_planner import GeminiPlanner, ReplayPlanner
from resumable_agent import CASES, InterruptedRun, run

class FeedbackTests(unittest.TestCase):
    def test_all_cases_wrong_then_right(self):
        with tempfile.TemporaryDirectory() as tmp:
            for case, config in CASES.items():
                result = run(case, ReplayPlanner(config['replay']), Path(tmp) / (case + '.json'))
                self.assertFalse(result['baseline']['passed'])
                self.assertEqual([a['status'] for a in result['attempts']], ['VERIFIED_FAIL', 'VERIFIED_PASS'])
                self.assertTrue(result['original_unchanged'])
                self.assertTrue(all(a['files_unchanged_except_patch'] for a in result['attempts']))

    def test_actual_process_interrupt_and_resume(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'state.json'
            command = [sys.executable, str(root / 'resumable_agent.py'), '--case', 'tax',
                       '--mode', 'replay', '--state', str(state)]
            interrupted = subprocess.run(command + ['--stop-after', '1'], capture_output=True, text=True)
            self.assertEqual(interrupted.returncode, 75, interrupted.stdout + interrupted.stderr)
            before = json.loads(state.read_text())
            self.assertEqual(before['verdict'], 'RUNNING')
            resumed = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
            after = json.loads(state.read_text())
            self.assertEqual(after['attempts'][0], before['attempts'][0])
            self.assertEqual(after['verdict'], 'VERIFIED_PASS')
            self.assertEqual(len(after['attempts']), 2)

    def test_changed_planner_refuses_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'state.json'
            with self.assertRaises(InterruptedRun):
                run('tax', ReplayPlanner(CASES['tax']['replay']), state, stop_after=1)
            with self.assertRaisesRegex(ValueError, 'Resume refused'):
                run('tax', ReplayPlanner(['subtotal']), state)

    def test_edited_success_checkpoint_cannot_bypass_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'state.json'
            planner = ReplayPlanner(CASES['tax']['replay'])
            run('tax', planner, state)
            saved = json.loads(state.read_text())
            saved['accepted_expression'] = 'subtotal'
            state.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, 'revalidation'):
                run('tax', planner, state)

    def test_completed_success_is_independently_rechecked(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'state.json'
            planner = ReplayPlanner(CASES['shipping']['replay'])
            first = run('shipping', planner, state)
            with patch.object(planner, 'propose', side_effect=AssertionError('No new proposal needed')):
                resumed = run('shipping', planner, state)
            self.assertTrue(resumed['resume_revalidation']['verification']['passed'])
            self.assertTrue(resumed['resume_revalidation']['files_unchanged_except_patch'])
            self.assertEqual(first['attempts'], resumed['attempts'])

    def test_changed_verifier_refuses_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'state.json'
            planner = ReplayPlanner(CASES['tax']['replay'])
            with self.assertRaises(InterruptedRun):
                run('tax', planner, state, stop_after=1)
            saved = json.loads(state.read_text())
            saved['binding']['verifier_sha256'] = {'resumable_agent.py': 'edited-verifier'}
            state.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, 'Resume refused'):
                run('tax', planner, state)

    def test_unsafe_and_excessive_candidates_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run('discount', ReplayPlanner(['__import__("os").getcwd()', 'subtotal'] * 2), Path(tmp) / 's.json')
            self.assertEqual(result['verdict'], 'VERIFIED_FAIL')
            self.assertEqual(len(result['attempts']), 3)
            self.assertEqual(result['attempts'][0]['status'], 'REJECTED')

    def test_model_feedback_and_structured_contract(self):
        class Response:
            output_text = '{"expression":"subtotal - discount","reason":"discount once"}'
        class Interactions:
            def create(self, **kwargs):
                self.request = kwargs
                return Response()
        class Client:
            interactions = Interactions()
        client = Client()
        planner = GeminiPlanner(client=client)
        context = {'attempts': [{'status': 'VERIFIED_FAIL'}]}
        self.assertEqual(planner.propose(context)['expression'], 'subtotal - discount')
        self.assertIn('VERIFIED_FAIL', client.interactions.request['input'])
        self.assertEqual(client.interactions.request['response_format']['mime_type'], 'application/json')

    def test_live_missing_key_never_falls_back(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'Live mode requires'):
                GeminiPlanner()
