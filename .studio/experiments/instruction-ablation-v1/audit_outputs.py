"""Check fixed audit targets and artifacts; no literary scores or model calls."""
from pathlib import Path
import json,re,hashlib
B=Path(__file__).resolve().parent;keys=json.loads((B/'condition-keys.json').read_text());task_ids=[x['id'] for x in json.loads((B/'assignments.json').read_text())]
def sections(t):
 ms=list(re.finditer(r'^## (F[12]-[PDC])[^\n]*$',t,re.M));assert [m[1] for m in ms]==task_ids
 return {m[1]:t[m.end():ms[i+1].start() if i+1<len(ms) else len(t)].strip() for i,m in enumerate(ms)}
fixture=(B/'inputs/fixtures.md').read_text();targets={}
for f in ['F1','F2']:
 s=fixture.split(f'### {f} audit target',1)[1].split('## F2',1)[0];targets[f]={f'L{m[1]}':m[2] for m in re.finditer(r'^\[L(\d+)\] (.*)$',s,re.M)}
expected={'F1':{'L1','L3','L6','L8'},'F2':{'L1','L4','L6','L8'}};results={};flags=[]
for run,key in keys.items():
 p=B/f'outputs/{run}.md'
 if not p.exists():continue
 parts=sections(p.read_text());row={'arm':key['arm'],'condition':key['condition'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'word_counts':{pid:len(t.split()) for pid,t in parts.items()},'audits':{}}
 for f in ['F1','F2']:
  raw=parts[f+'-C'];start=raw.find('{')
  try:a,end=json.JSONDecoder().raw_decode(raw[start:])
  except Exception as e:row['audits'][f]={'parse_error':str(e)};flags.append({'run':run,'task':f+'-C','kind':'audit JSON parse error'});continue
  errors=a.get('errors',[]);line=lambda x:x.replace('[','').replace(']','').strip();found=[line(x['line']) for x in errors];controls=set(targets[f])-expected[f];validpreserve=[line(x) for x in a.get('preserve',[])];wrong=set(found)-expected[f]
  for e in errors:
   lid=line(e['line']);q=e.get('quote','')
   if q not in targets[f].get(lid,''):flags.append({'run':run,'task':f+'-C','line':lid,'kind':'quote not exact in cited line','quote':q})
   if not 4<=len(q.split())<=14:flags.append({'run':run,'task':f+'-C','line':lid,'kind':'quote length outside 4–14 words','quote':q})
  row['audits'][f]={'identified_seeded_lines':sorted(set(found)&expected[f]),'missed_seeded_lines':sorted(expected[f]-set(found)),'false_positive_lines':sorted(wrong),'valid_controls':sorted(controls),'valid_controls_preserved':sorted(controls&set(validpreserve)),'duplicate_error_lines':len(found)-len(set(found)),'errors':errors,'queries':a.get('queries',[])}
 results[run]=row
(B/'audit-results.json').write_text(json.dumps({'expected_errors_per_fixture':4,'valid_controls_per_fixture':6,'note':'Line identification counts require manual confirmation of diagnosis and repair. Queries on valid lines are not definite false positives.','runs':results,'flags':flags},indent=2,ensure_ascii=False)+'\n')
print('Artifacts checked',len(results),'of',len(keys),'format/evidence flags',len(flags))
for run,row in results.items():print(run,{f:(len(x.get('missed_seeded_lines',[])),len(x.get('false_positive_lines',[]))) if 'parse_error' not in x else 'parse-error' for f,x in row['audits'].items()})
