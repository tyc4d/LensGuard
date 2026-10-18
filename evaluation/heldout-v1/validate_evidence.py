"""Offline integrity/completeness validation; not an acceptance-success assertion."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
raw=(P/'manifest.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==(P/'manifest.sha256').read_text().split()[0]
m=json.loads(raw);seen=set();complete=0;failed=0;missing=[]
for c in m['cases']:
 assert hashlib.sha256((P/c['image']).read_bytes()).hexdigest()==c['sha256']
 for mode in ('on','off'):
  label=c['id']+'_'+mode;path=P/'runs'/(label+'.json')
  if not path.exists():missing.append(label);continue
  s=json.loads(path.read_text());r=json.loads((P/'runs'/(label+'_request.json')).read_text())
  assert r['manifest_sha256']==hashlib.sha256(raw).hexdigest();assert r['requested_at_utc']>m['frozen_at_utc']
  assert s['id'] not in seen;seen.add(s['id']);assert s['guard_enabled']==(mode=='on')
  assert r['fields']['user_request']==c['request'];assert r['image_sha256']==c['sha256']
  assert s['status']!='running';complete+=1;failed+=s['status']=='failed'
assert len(list((P/'runs').glob('*_request.json')))<=m['max_post_requests']
print(json.dumps({'manifest_integrity':'valid','completed_records':complete,'failed_runs':failed,'missing_records':missing,'meaning':'Integrity and completeness only; see adjudication for correctness and authority outcomes.'},indent=2))
if missing:raise SystemExit(1)
