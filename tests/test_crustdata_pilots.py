import io
import json
import unittest
from urllib.error import HTTPError
from crustdata_pilots import discover, normalize, ENDPOINT, VERSION


class CrustdataTests(unittest.TestCase):
    def test_request_is_bounded_and_report_excludes_credentials(self):
        calls = []
        def opener(request, timeout):
            calls.append(request)
            self.assertEqual(timeout, 30)
            self.assertEqual(request.full_url, ENDPOINT)
            self.assertEqual(request.get_header('X-api-version'), VERSION)
            body = json.loads(request.data)
            self.assertEqual(body['limit'], 5)
            self.assertNotIn('cursor', body)
            self.assertTrue(all(f.startswith('basic_info.') for f in body['fields']))
            return io.BytesIO(json.dumps({'companies': [{
                'crustdata_company_id': 1, 'basic_info': {'name': 'Synthetic fixture'},
                'private_contact': 'must not persist'}]}).encode())
        report = discover('test-placeholder', opener)
        self.assertEqual(len(calls), 1)
        self.assertNotIn('test-placeholder', json.dumps(report))
        self.assertNotIn('private_contact', json.dumps(report))
        self.assertEqual(report['customer_commitments'], 0)
        self.assertIsNone(report['credits_used'])

    def test_http_failure_does_not_retry_or_expose_provider_body(self):
        calls = []
        def opener(request, timeout):
            calls.append(request)
            raise HTTPError(ENDPOINT, 429, 'private error content', {}, None)
        with self.assertRaisesRegex(RuntimeError, '^Crustdata returned HTTP 429; no automatic retry$'):
            discover('test-placeholder', opener)
        self.assertEqual(len(calls), 1)

    def test_invalid_result_rejected_and_empty_search_is_valid(self):
        for bad in (None, [{}], [None], [{'crustdata_company_id': True, 'basic_info': {}}]):
            with self.assertRaises(ValueError):
                normalize(bad)
        self.assertEqual(normalize([]), [])

    def test_duplicate_company_ids_are_collapsed(self):
        record = {'crustdata_company_id': 1, 'basic_info': {'name': 'Synthetic fixture'}}
        self.assertEqual(len(normalize([record, record])), 1)
