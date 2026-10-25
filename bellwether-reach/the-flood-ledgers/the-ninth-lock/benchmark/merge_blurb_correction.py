"""Merge fresh P8 judgments into derived reviews; retain every original file."""
import hashlib,json,re
from pathlib import Path
B=Path(__file__).resolve().parent
old=json.loads((B/'blind-keys.json').read_text());new=json.loads((B/'blurb-correction-keys.json').read_text());provenance={}
for jid,key in old.items():
 original=B/f'reviews/{jid}.json';review=json.loads(original.read_text())
 if jid in new:
  p=B/f'reviews-corrected/{jid}.json';fresh=json.loads(p.read_text());assert [x['phase'] for x in fresh['phases']]==['P8'];phase=fresh['phases'][0];expected=set(new[jid]['labels']);flat=[x for tier in phase['tiers'] for x in tier];assert len(flat)==6 and set(flat)==expected
  inv={cid:label for label,cid in key['labels'].items()};remap={label:inv[cid] for label,cid in new[jid]['labels'].items()}
  phase['tiers']=[[remap[x] for x in tier] for tier in phase['tiers']]
  for e in phase['evidence']:e['candidate']=remap[e['candidate']]
  review['phases']=[phase if x['phase']=='P8' else x for x in review['phases']]
  review['coverage']='P1–P7: original full-packet independent review. P8: fresh six-blurb packet, with runtime metadata excluded from blurb text. See provenance.'
  review['provenance']={'original':str(original.relative_to(B)),'P8_replacement':str(p.relative_to(B)),'label_map':'Original blind-key labels restored by author-ID mapping; no preference or evidence content altered.'}
  provenance[jid]=dict(review['provenance'])
 else:provenance[jid]={'original':str(original.relative_to(B)),'P8':'Unchanged because this exact-model reviewer never saw either Kimi artifact; its candidate set is identical.'}
 (B/f'effective-reviews/{jid}.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
(B/'effective-review-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print('Merged P8 only, retaining original reviews and all original fiction.')
