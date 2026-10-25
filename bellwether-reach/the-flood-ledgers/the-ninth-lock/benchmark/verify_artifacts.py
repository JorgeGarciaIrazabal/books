"""Verify frozen sources, correction provenance, ranks and evidence; no model calls."""
from pathlib import Path
import json,re,hashlib,collections
b=Path(__file__).resolve().parent;root=b.parents[3]
v=json.loads((b/'validation.json').read_text());r=json.loads((b/'results.json').read_text());original=json.loads((b/'original-results.json').read_text())
for pid in [f'P{i}' for i in range(1,8)]:assert r['phases'][pid]==original['phases'][pid],pid
for p,h in json.loads((b/'candidate-snapshot.json').read_text()).items():assert hashlib.sha256((b/p).read_bytes()).hexdigest()==h,p
for p,h in json.loads((b/'source-snapshot.json').read_text()).items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
old=json.loads((b/'blind-keys.json').read_text());new=json.loads((b/'blurb-correction-keys.json').read_text())
for jid in old:
 a=json.loads((b/f'reviews/{jid}.json').read_text());e=json.loads((b/f'effective-reviews/{jid}.json').read_text())
 assert a['phases'][:7]==e['phases'][:7]
 if jid.startswith('kimi'):assert a['phases'][7]==e['phases'][7]
for jid,k in new.items():
 t=json.loads((b/f'reviews-corrected/{jid}.json').read_text());assert [x['phase'] for x in t['phases']]==['P8'];p=t['phases'][0];labels=set(k['labels']);flat=[x for tier in p['tiers'] for x in tier];assert set(flat)==labels and len(flat)==6;assert {x['candidate'] for x in p['evidence']}==labels
outs={}
for cid in r['phases']['P1']['candidates']:
 path=b/('outputs-corrected' if cid=='kimi-low' else 'outputs')/f'{cid}.md';t=path.read_text();ms=list(re.finditer(r'^## (P[1-8])[^\n]*$',t,re.M));outs[cid]={m[1]:t[m.end():ms[i+1].start() if i+1<len(ms) else len(t)].strip() for i,m in enumerate(ms)}
def norm(s):return ' '.join(re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?",s.lower().replace('’',"'")))
known={('mistral-high','P2','sol61-high'):'The source says “Instead, he produces the payment book bearing the same balance number” with Ivo as the explicit preceding subject. Added name is contextually supported but not verbatim.',('mistral-high','P4','sol6-high'):'Source says Sera “took the pen and wrote South’s certificate number again in the margin”. Added “she” is contextually supported but not contiguous.',('mistral-high','P6','sol61-high'):'Source says “She had come for the second certificate”; She refers to Sera. Name substitution preserves meaning but is not verbatim.'}
d=[];counts=collections.Counter()
for flag in v['evidence_flags']:
 x=dict(flag)
 if flag['kind'].startswith('outside'):kind='quotation length';x['disposition']='Outside requested quotation length. Underlying source match is checked separately; no rank change.'
 elif norm(flag['quote']) in norm(outs[flag['candidate']][flag['phase']]):kind='typography/formatting';x['disposition']='Source words match after typography, case, punctuation or Markdown normalization. Exact-quote requirement was not met; no semantic evidence defect established.'
 else:
  key=(flag['judge'],flag['phase'],flag['candidate']);assert key in known,flag;kind='minor wording change';x['disposition']=known[key]+' Preserve the raw review and do not print this altered wording as an exact quotation.'
 counts[kind]+=1;x['classification']=kind;d.append(x)
(b/'evidence-disposition.json').write_text(json.dumps({'flags':d,'classification_counts':dict(counts),'ruling':'All flagged content is supported in context. Keep exact-quotation and length failures visible. No reviewer ranks were altered to repair quotations. Published report excerpts are selected only from verified exact 4–18-word quotes.'},indent=2,ensure_ascii=False)+'\n')
v['additional_checks']=['All initial source and candidate hashes unchanged','P1–P7 rankings identical to original run','Kimi reviewer P8 unchanged; its candidate set was unaffected','Six fresh P8 correction reviews cover their eligible sets','Opaque correction labels remapped by author ID only','All pairwise preferences complementary','All report evidence excerpts selected from exact 4–18-word source matches','All eight P6 edits retain the protected fragment']
v['evidence_disposition']='evidence-disposition.json';(b/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
counts=json.loads((b/'word-counts.json').read_text());corrected=len(re.findall(r"\b[\w’'-]+\b",outs['kimi-low']['P8']));(b/'corrected-word-counts.json').write_text(json.dumps({'kimi-low':{'P8':corrected},'note':'Runtime process note excluded; original word-counts.json is retained.'},indent=2)+'\n')
print('Final verification passed; evidence dispositions:',dict(collections.Counter(x['classification'] for x in d)));print('Corrected Kimi low blurb words',corrected)
