"""Optional pilot-company discovery. No outreach or repair verdicts are generated."""
import argparse
import getpass
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ENDPOINT = 'https://api.crustdata.com/company/search'
VERSION = '2025-11-01'
QUERY = 'Software companies building AI coding agents, software testing or developer tools'
FIELDS = ['basic_info.name', 'basic_info.primary_domain', 'basic_info.description']


def normalize(companies):
    """Keep only company fields; reject malformed responses and deduplicate IDs."""
    if not isinstance(companies, list) or len(companies) > 5:
        raise ValueError('Invalid company result list')
    result, seen = [], set()
    for company in companies:
        if not isinstance(company, dict):
            raise ValueError('Invalid company record')
        cid, info = company.get('crustdata_company_id'), company.get('basic_info')
        if type(cid) is not int or cid <= 0 or not isinstance(info, dict):
            raise ValueError('Missing company identity')
        record = {'crustdata_company_id': cid}
        for field in ('name', 'primary_domain', 'description'):
            value = info.get(field)
            if value is not None and (not isinstance(value, str) or len(value) > 10000):
                raise ValueError('Invalid company field')
            record[field] = value
        if cid not in seen:
            seen.add(cid)
            result.append(record)
    return result


def discover(api_key, opener=urlopen):
    if not api_key or any(c in api_key for c in '\r\n'):
        raise ValueError('Configure CRUSTDATA_API_KEY privately')
    body = {'search': {'query': QUERY, 'mode': 'hybrid'}, 'fields': FIELDS, 'limit': 5}
    request = Request(ENDPOINT, data=json.dumps(body).encode(), method='POST', headers={
        'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json',
        'x-api-version': VERSION})
    started = time.monotonic()
    try:
        with opener(request, timeout=30) as response:
            raw = response.read(1000001)
        if len(raw) > 1000000:
            raise ValueError('Response too large')
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError('Invalid response envelope')
        companies = normalize(data.get('companies'))
    except HTTPError as error:
        raise RuntimeError(f'Crustdata returned HTTP {error.code}; no automatic retry') from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError('Crustdata connection failed; no automatic retry') from None
    except (ValueError, UnicodeError):
        raise RuntimeError('Crustdata response failed validation') from None
    return {'source': 'Crustdata company search', 'endpoint': ENDPOINT,
            'api_version': VERSION, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'query': QUERY, 'status': 'LIVE_RESEARCH_RESULTS',
            'latency_ms': round((time.monotonic() - started) * 1000, 1),
            'companies': companies, 'requests': 1, 'pagination_followed': False,
            'credits_used': None, 'customer_commitments': 0,
            'limitations': 'Search matches are research candidates, not customers or verified demand. '
                            'No contact details, outreach, revenue forecast changes or repair decisions.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='artifacts/crustdata-pilots-private.json')
    args = parser.parse_args()
    key = os.environ.get('CRUSTDATA_API_KEY') or getpass.getpass('Crustdata API key (hidden): ')
    try:
        report = discover(key)
    except (ValueError, RuntimeError) as error:
        print(str(error))
        return 1
    finally:
        key = None
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"Saved {len(report['companies'])} live research candidates to {path}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
