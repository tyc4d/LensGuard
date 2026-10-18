"""Opt-in, standard-library live runner. Default mode is offline manifest verification.

Each case/mode is POSTed at most once. An uncertain POST is never retried.
Use existing Demo only; no credentials, configuration, or external action service.
"""
import argparse, datetime, hashlib, json, time, uuid, urllib.request, urllib.error
from pathlib import Path
P=Path(__file__).resolve().parent

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def get_json(url):
 with urllib.request.urlopen(urllib.request.Request(url,method='GET'),timeout=40) as r:return json.load(r)
def multipart(fields,image):
 boundary='LensGuardHeldout'+uuid.uuid4().hex;chunks=[]
 for k,v in fields.items():chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
 chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{image.name}"\r\nContent-Type: image/png\r\n\r\n'.encode()+image.read_bytes()+b'\r\n')
 chunks.append(f'--{boundary}--\r\n'.encode())
 return b''.join(chunks),{'Content-Type':'multipart/form-data; boundary='+boundary}
def verify():
 raw=(P/'manifest.json').read_bytes();expected=(P/'manifest.sha256').read_text().split()[0]
 assert hashlib.sha256(raw).hexdigest()==expected,'Manifest changed after preregistration'
 m=json.loads(raw)
 for c in m['cases']:assert hashlib.sha256((P/c['image']).read_bytes()).hexdigest()==c['sha256'],c['id']+' image hash mismatch'
 assert len(m['run_order'])==m['max_post_requests']==16
 return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-live',action='store_true');args=ap.parse_args();m=verify()
 print('Verified fixed manifest and 8 fixture hashes. Planned requests:',len(m['run_order']),flush=True)
 if not args.execute_live:
  print('Offline only. Pass --execute-live to explicitly execute existing public Demo requests.');return
 out=P/'runs';out.mkdir(exist_ok=True);cases={c['id']:c for c in m['cases']}
 for entry in m['run_order']:
  c=cases[entry['case_id']];guard=entry['guard_enabled'];label=c['id']+('_on' if guard else '_off');record=out/(label+'_request.json')
  started=time.monotonic();fields={'user_request':c['request'],'source':'uploaded_image','guard_enabled':str(guard).lower(),'scenario_id':c['scenario'],'model_profile':m['model_profile']}
  metadata={'registered_case':c['id'],'guard_enabled':guard,'requested_at_utc':now(),'manifest_sha256':(P/'manifest.sha256').read_text().split()[0],'image_sha256':c['sha256'],'fields':fields,'endpoint':m['target']+'api/run'}
  if record.exists():
   if any((out/(label+suffix)).exists() for suffix in ('_submission_error.json','_observation_error.json')):
    raise SystemExit('UNRESOLVED_ATTEMPT '+label+'; inspect the recorded error before any further POSTs')
   try:
    terminal=json.loads((out/(label+'.json')).read_text())
    complete=isinstance(terminal,dict) and terminal.get('status') in ('completed','failed') and isinstance(terminal.get('id'),str)
   except (OSError,ValueError):
    complete=False
   if not complete:
    raise SystemExit('UNRESOLVED_ATTEMPT '+label+'; no valid terminal record, no further POSTs issued')
   print('SKIP completed POST',label,flush=True);continue
  # Exclusive marker is written before sending; no POST retry even on uncertainty.
  with record.open('x') as f:json.dump(metadata,f,indent=2)
  data,headers=multipart(fields,P/c['image'])
  try:
   req=urllib.request.Request(m['target']+'api/run',data=data,headers=headers,method='POST')
   with urllib.request.urlopen(req,timeout=40) as r:body=r.read().decode();status=r.status
   (out/(label+'_initial.json')).write_text(body);s=json.loads(body);rid=s['id']
  except Exception as e:
   (out/(label+'_submission_error.json')).write_text(json.dumps({'type':type(e).__name__,'http_status':getattr(e,'code',None),'at_utc':now(),'post_retried':False,'observation_status':'inconclusive'},indent=2))
   raise SystemExit('SUBMISSION_STOP '+label+' '+type(e).__name__+'; no further POSTs issued')
  print('START',label,rid,flush=True)
  poll_deadline=time.monotonic()+600
  def stop_observation(kind,detail):
   artifact={'run_id':rid,'at_utc':now(),'observation_status':'inconclusive',
             'reason':kind,'detail':detail,'post_retried':False,
             'note':'A retrieval failure is not proof of an inference failure. Stop the suite; inspect this existing Run ID before resuming.'}
   (out/(label+'_observation_error.json')).write_text(json.dumps(artifact,indent=2))
   raise SystemExit('OBSERVATION_STOP '+label+' '+kind+'; no further POSTs issued')
  while s.get('status')=='running':
   if time.monotonic()>=poll_deadline:stop_observation('poll_deadline','No terminal state observed within the 600-second retrieval window.')
   time.sleep(3)
   try:s=get_json(m['target']+'api/run/'+rid)
   except urllib.error.HTTPError as e:
    if 400<=e.code<500 and e.code not in (408,429):
     stop_observation('nonretryable_http_'+str(e.code),'The public run endpoint rejected retrieval. No access restriction will be bypassed.')
    print('GET_RETRY',label,'HTTP',e.code,flush=True);continue
   except (urllib.error.URLError,TimeoutError) as e:
    print('GET_RETRY',label,type(e).__name__,flush=True);continue
  (out/(label+'.json')).write_text(json.dumps(s,indent=2,ensure_ascii=False))
  timing={'completed_at_utc':now(),'client_wall_seconds':round(time.monotonic()-started,3),'run_id':rid};(out/(label+'_client.json')).write_text(json.dumps(timing,indent=2))
  brief={'case':label,'id':rid,'status':s.get('status'),'stage':s.get('stage'),'answer':s.get('final_answer'),'action':s.get('action'),'decision':s.get('decision'),'review':s.get('second_opinion'),'error':s.get('error'),'server_ms':s.get('timings',{}).get('demo_runtime_ms')}
  print('RESULT',json.dumps(brief,ensure_ascii=False),flush=True)
 print('COMPLETE all preregistered requests attempted once.',flush=True)
if __name__=='__main__':main()
