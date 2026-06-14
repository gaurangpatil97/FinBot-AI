import os, json, requests, sys
base = os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')
# Get companies
res = requests.get(f'{base}/api/v1/companies')
if res.status_code != 200:
    print('Failed to get companies', res.status_code)
    sys.exit(1)
companies = res.json()
if not isinstance(companies, list):
    print('Unexpected response format')
    sys.exit(1)
if not companies:
    print('No companies found')
    sys.exit(1)
company = companies[0]
slug = company.get('slug')
print('Using company slug:', slug)
# Create session
res = requests.post(f'{base}/api/v1/sessions', json={'company_slug': slug, 'title': 'Test Session'})
if res.status_code != 200:
    print('Failed to create session', res.status_code, res.text)
    sys.exit(1)
session = res.json()
session_id = session.get('session_id') or session.get('id') or session.get('sessionId')
print('Created session id:', session_id)
# Export transcript PDF
export_res = requests.get(f'{base}/api/v1/sessions/{session_id}/export/transcript')
print('Export status:', export_res.status_code)
if export_res.status_code == 200:
    with open('test_transcript.pdf', 'wb') as f:
        f.write(export_res.content)
    print('PDF saved as test_transcript.pdf')
else:
    print('Export failed', export_res.text)
