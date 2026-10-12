"""Structured, bounded Gemini proposals. Never executes generated commands."""
import json
import os
import re

def parse_gateway_proposal(content):
    """Accept JSON or one complete JSON fence; never mine prose for code."""
    if not isinstance(content, str) or len(content) > 6000:
        raise ValueError('Invalid gateway response body')
    text = content.strip()
    fenced = re.fullmatch(r'```(?:json)?[ \t]*\r?\n(.*?)\r?\n```', text, re.DOTALL)
    proposal = json.loads(fenced.group(1) if fenced else text)
    if not isinstance(proposal, dict) or set(proposal) != {'expression','reason'} or not all(isinstance(v,str) for v in proposal.values()):
        raise ValueError('Malformed gateway proposal')
    if len(proposal['reason']) > 1500:
        raise ValueError('Oversized explanation')
    return proposal, 'complete_json_fence' if fenced else 'plain_json'

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

class LiteLLMPlanner:
    """Hackathon OpenAI-compatible gateway, with local JSON/DSL validation.

    The gateway is not assumed to enforce structured-output schemas. Provider
    output must pass our JSON validation and the independent arithmetic gate.
    """
    BASE_URL = 'https://litellm.vision.aivar.app/v1'
    MODELS = {'nova-micro', 'nova-lite', 'nova-pro', 'nova-2-lite',
              'claude-haiku', 'claude-sonnet-4.6', 'claude-opus-4.6'}

    def __init__(self, model='claude-haiku', api_key=None, client=None):
        if model not in self.MODELS:
            raise ValueError('Choose a model from the organizer-provided gateway list')
        self.model = model
        self.identity = 'litellm:' + self.BASE_URL + ':' + model
        self.last_usage = None
        if client is None:
            key = api_key or os.getenv('LITELLM_API_KEY')
            if not key:
                raise ValueError('Live gateway mode requires LITELLM_API_KEY; no replay fallback')
            from openai import OpenAI
            client = OpenAI(base_url=self.BASE_URL, api_key=key, timeout=30.0, max_retries=0)
        self.client = client

    def propose(self, context):
        import time
        prompt = ('Repair the one arithmetic expression in this trusted billing fixture. '
                  'Respond with exactly one JSON object containing only string fields '
                  '"expression" and "reason". No markdown or extra text. '
                  'The expression may contain only the listed variables, numeric literals, '
                  '+ - * / and parentheses. Never change acceptance tests or return commands. '
                  'Use prior test feedback to revise incorrect proposals.\n' + json.dumps(context, sort_keys=True))
        started = time.monotonic()
        result = self.client.chat.completions.create(model=self.model,
            messages=[{'role':'user','content':prompt}], max_tokens=384)
        usage = getattr(result, 'usage', None)
        self.last_usage = {'provider':'hackathon-litellm','model':self.model,
            'latency_ms':round((time.monotonic()-started)*1000,2),
            'prompt_tokens':getattr(usage,'prompt_tokens',None),
            'completion_tokens':getattr(usage,'completion_tokens',None),
            'total_tokens':getattr(usage,'total_tokens',None),
            'max_output_tokens':384, 'sdk_auto_retries':0,
            'cost_usd':None, 'cost_note':'No dollar cost claimed without provider billing evidence'}
        choice = result.choices[0]
        if choice.finish_reason != 'stop':
            raise ValueError('Incomplete model response; proposal was not applied')
        proposal, normalization = parse_gateway_proposal(choice.message.content)
        self.last_usage['response_normalization'] = normalization
        return proposal
