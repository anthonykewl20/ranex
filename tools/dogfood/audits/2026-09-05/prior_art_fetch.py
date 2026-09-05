import concurrent.futures,hashlib,json,urllib.request
from pathlib import Path
out=Path('.local/release-audit')
inputs=json.loads((out/'prior-art-fetch-inputs.json').read_text())
def fetch(row):
 result=dict(row)
 local=Path(row['path']).read_bytes()
 result['local_sha256']=hashlib.sha256(local).hexdigest()
 try:
  with urllib.request.urlopen(row['url'],timeout=30) as response:
   data=response.read(10_000_001)
   result.update(http_status=response.status,final_url=response.url,remote_bytes=len(data),remote_sha256=hashlib.sha256(data).hexdigest())
  result['status']='MATCH' if data==local else 'DIFFERENT'
 except Exception as error: result.update(status='UNVERIFIED',error=f'{type(error).__name__}: {error}')
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 rows=list(pool.map(fetch,inputs))
result={'schema':'ranex-prior-art-origin-check-v1','date':'2026-09-05','method':'Refetch every unambiguous filename plus raw.githubusercontent.com URL on one NOTICE line. Compare complete bytes over verified HTTPS. Other provenance formats are outside this automated subset. A difference is not automatically a defect (excerpt/adaptation may be documented).','results':rows}
(out/'prior-art-fetch.json').write_text(json.dumps(result,indent=2)+'\n')
from collections import Counter
print(Counter(r['status'] for r in rows))
for r in rows:
 if r['status']!='MATCH': print(r['status'],r['path'],r.get('error',''))
