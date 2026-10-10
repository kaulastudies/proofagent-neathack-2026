import unittest
from agent import execute

class AgentTests(unittest.TestCase):
    def test_recovery_success(self):
        run = execute("transient_failure")
        self.assertEqual(run["verdict"], "VERIFIED_PASS")
        self.assertEqual(run["attempts"], 2)
        self.assertTrue(any(e["step"] == "recover" for e in run["events"]))

    def test_incorrect_spec_stays_failed(self):
        run = execute("incorrect_output")
        self.assertEqual(run["verdict"], "VERIFIED_FAIL")
        self.assertFalse(run["artifact"]["checks"]["matches_acceptance_spec"])

    def test_success(self):
        self.assertEqual(execute("success")["verdict"], "VERIFIED_PASS")

    def test_bounded_retries(self):
        run = execute("transient_failure", max_attempts=1)
        self.assertEqual(run["verdict"], "VERIFIED_FAIL")
        self.assertEqual(run["attempts"], 1)

if __name__ == "__main__":
    unittest.main()
