"""Structured, bounded Gemini proposals. Never executes generated commands."""
import json
import os

class GeminiPlanner:
    def __init__(self, model='gemini-3.8-flash', api_key=None, client=None):
        self.model = model
        self.identity = 'gemini:' + model
        if client is None:
            key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if not key:
                raise ValueError('Live mode requires GEMINI_API_KEY. Offline replay is a separate mode.')
            from google import genai
            client = genai.Client(api_key=key, http_options={'timeout': 30000})
        self.client = client

    def propose(self, context):
        schema = {'type': 'object', 'properties': {
            'expression': {'type': 'string'}, 'reason': {'type': 'string'}},
            'required': ['expression', 'reason']}
        prompt = ('Repair the arithmetic expression in this trusted billing fixture. '
                  'Return only one expression using the allowed variables, numeric literals, '
                  '+ - * / and parentheses. Do not return code, commands, or alter tests. '
                  'Use independent-test feedback to revise earlier failures.\n' +
                  json.dumps(context, sort_keys=True))
        result = self.client.interactions.create(model=self.model, input=prompt,
            response_format={'type': 'text', 'mime_type': 'application/json', 'schema': schema})
        proposal = json.loads(result.output_text)
        if set(proposal) != {'expression', 'reason'} or not all(isinstance(v, str) for v in proposal.values()):
            raise ValueError('Malformed structured proposal')
        return proposal

class ReplayPlanner:
    """Explicitly scripted proposals for reproducible offline regression/demo runs."""
    def __init__(self, proposals):
        self.proposals = list(proposals)
        self.identity = 'offline-replay:' + json.dumps(self.proposals, separators=(',', ':'))
    def propose(self, context):
        index = len(context['attempts'])
        if index >= len(self.proposals):
            raise ValueError('Offline replay exhausted')
        return {'expression': self.proposals[index], 'reason': 'Scripted offline replay; not model reasoning'}
