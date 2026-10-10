import tempfile
import unittest
from pathlib import Path

from repair_agent import repair_repo


FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures' / 'buggy_calculator'


class RepositoryRepairTests(unittest.TestCase):
    def test_failing_baseline_becomes_verified_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = repair_repo(FIXTURE, Path(tmp) / 'candidate')
            self.assertFalse(result['baseline']['passed'])
            self.assertTrue(result['after']['passed'])
            self.assertEqual(result['verdict'], 'VERIFIED_PASS')
            self.assertIn('subtotal - discount', result['patch'])

    def test_transient_failure_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = repair_repo(FIXTURE, Path(tmp) / 'candidate', simulate_timeout=True)
            self.assertEqual(result['verdict'], 'VERIFIED_PASS')
            self.assertTrue(any(e['action'] == 'recover_retry' for e in result['events']))

    def test_exhausted_retry_stops_without_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = repair_repo(FIXTURE, Path(tmp) / 'candidate', max_attempts=1, simulate_timeout=True)
            self.assertEqual(result['verdict'], 'VERIFIED_FAIL')
            self.assertEqual(result['before_sha256'], result['after_sha256'])

    def test_original_untouched(self):
        before = (FIXTURE / 'calculator.py').read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            repair_repo(FIXTURE, Path(tmp) / 'candidate')
        self.assertEqual(before, (FIXTURE / 'calculator.py').read_bytes())

    def test_unknown_defect_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source'
            import shutil
            shutil.copytree(FIXTURE, source)
            path = source / 'calculator.py'
            path.write_text('def calculate_total(prices, discount=0):\n    return 999\n', encoding='utf-8')
            result = repair_repo(source, Path(tmp) / 'candidate')
            self.assertEqual(result['verdict'], 'VERIFIED_FAIL')
            self.assertEqual(result['before_sha256'], result['after_sha256'])


if __name__ == '__main__':
    unittest.main()
