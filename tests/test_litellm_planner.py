import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from model_planner import LiteLLMPlanner
from resumable_agent import run

class GatewayTests(unittest.TestCase):
    def client(self, content, finish='stop'):
        response = SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish,
            message=SimpleNamespace(content=content))], usage=SimpleNamespace(
            prompt_tokens=150, completion_tokens=20, total_tokens=170))
        class Completions:
            def create(self, **kwargs):
                self.request = kwargs
                return response
        completions=Completions()
        return SimpleNamespace(chat=SimpleNamespace(completions=completions))

    def test_json_and_feedback_and_output_cap(self):
        client=self.client('{"expression":"subtotal - discount","reason":"apply once"}')
        planner=LiteLLMPlanner(client=client)
        self.assertEqual(planner.propose({'attempts':[{'status':'VERIFIED_FAIL'}]})['expression'],'subtotal - discount')
        request=client.chat.completions.request
        self.assertEqual(request['max_tokens'],384)
        self.assertIn('VERIFIED_FAIL',request['messages'][0]['content'])
        self.assertEqual(planner.last_usage['total_tokens'],170)
        self.assertIsNone(planner.last_usage['cost_usd'])

    def test_truncated_and_non_json_never_applied(self):
        for content,finish in [('{"expression":','length'),('not JSON','stop')]:
            with self.subTest(finish=finish), self.assertRaises(ValueError):
                LiteLLMPlanner(client=self.client(content,finish)).propose({})

    def test_generated_call_rejected_by_independent_gate(self):
        # JSON quoting must remain valid to reach the syntax gate.
        import json
        client=self.client(json.dumps({'expression':'__import__("os").getcwd()','reason':'unsafe'}))
        with tempfile.TemporaryDirectory() as tmp:
            result=run('discount',LiteLLMPlanner(client=client),Path(tmp)/'state.json',max_attempts=1)
        self.assertEqual(result['verdict'],'VERIFIED_FAIL')
        self.assertEqual(result['attempts'][0]['status'],'REJECTED')
        self.assertEqual(result['attempts'][0]['model_usage']['total_tokens'],170)

    def test_missing_key_and_unknown_model_stop(self):
        with patch.dict('os.environ',{},clear=True), self.assertRaises(ValueError):
            LiteLLMPlanner()
        with self.assertRaises(ValueError):
            LiteLLMPlanner(model='unapproved-model',client=self.client('{}'))
