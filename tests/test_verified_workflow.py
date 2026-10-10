import tempfile
import unittest
from pathlib import Path
from verified_workflow import verify_candidates

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/buggy_calculator'

class VerifiedWorkflowTests(unittest.TestCase):
    def run_candidates(self, candidates):
        with tempfile.TemporaryDirectory() as temp:
            return verify_candidates(FIXTURE, candidates, Path(temp) / 'report.json')

    def test_rejects_false_green_then_accepts_repair(self):
        result = self.run_candidates(['subtotal', 'subtotal - discount'])
        self.assertEqual(result['attempts'][0]['status'], 'VERIFIED_FAIL')
        self.assertEqual(result['attempts'][1]['status'], 'VERIFIED_PASS')
        self.assertTrue(result['original_unchanged'])
        self.assertTrue(all(a['tests_unchanged'] for a in result['attempts']))

    def test_no_acceptable_candidate_returns_failure(self):
        self.assertEqual(self.run_candidates(['subtotal', '999'])['verdict'], 'VERIFIED_FAIL')

    def test_generated_calls_are_rejected(self):
        result = self.run_candidates(['__import__("os").system("echo bad")'])
        self.assertEqual(result['verdict'], 'VERIFIED_FAIL')
        self.assertEqual(result['attempts'][0]['status'], 'REJECTED')
