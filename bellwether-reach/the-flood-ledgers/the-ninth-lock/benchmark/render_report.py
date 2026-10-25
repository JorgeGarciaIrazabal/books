"""Render the recorded benchmark evidence; no model or agent calls."""
import json,re
from pathlib import Path
B=Path(__file__).resolve().parent
r=json.loads((B/'results.json').read_text());phases=json.loads((B/'phases.json').read_text());keys=json.loads((B/'blind-keys.json').read_text());manifest=json.loads((B/'run-manifest.json').read_text())
review_dir=B/r.get('review_set','reviews')
names={'sol61-medium':'GPT-6.1 Sol medium','sol61-high':'GPT-6.1 Sol high','sol6-medium':'GPT-6 Sol medium','sol6-high':'GPT-6 Sol high','kimi-low':'Kimi K3 low','kimi-high':'Kimi K3 high','mistral-none':'Mistral Large 4 none','mistral-high':'Mistral Large 4 high'}
short={'sol61-medium':'S61m','sol61-high':'S61h','sol6-medium':'S6m','sol6-high':'S6h','kimi-low':'Kl','kimi-high':'Kh','mistral-none':'Mn','mistral-high':'Mh'}
def tiers(stats):
 groups=[]
 for c,s in sorted(stats.items(),key=lambda x:-x[1]['mean_preference']):
  if groups and abs(groups[-1][0]-s['mean_preference'])<1e-9:groups[-1][1].append(c)
  else:groups.append((s['mean_preference'],[c]))
 return ' > '.join(' = '.join(short[c] for c in cs) for _,cs in groups)
def stable(v):return all(set(x)==set(v['top']) for x in v['leave_one_reviewer_model_out'].values())
text='# Writing model benchmark — The Ninth Lock\n\nCompleted screening pilot: **64 phase samples, eight full reviewer sessions plus six fresh blurb comparisons, four model IDs, two settings per model**. Each sample is ranked by six sessions from the three other model IDs. All results below apply to this fixture.\n\n'
text+='| Phase | Leading sample(s) in combined peer preference | Remove-one-reviewer sensitivity |\n| --- | --- | --- |\n'
for p in phases:
 v=r['phases'][p['id']];text+=f'| {p["title"]} | '+', '.join(names[c] for c in v['top'])+' | '+('Same leader(s) after every removal' if stable(v) else 'Leader changes after at least one removal')+' |\n'
text+='\nTreat these as trial assignments for the next writing round. Where removing a reviewer model changes the leader, keep the leading alternatives in contention. This benchmark does not justify permanent default-model changes by itself.\n\n'
text+='## Full condition rankings\n\nAbbreviations: '+ '; '.join(f'**{short[c]}** = {names[c]}' for c in names)+'. `=` means equal combined preference; `>` means higher combined preference, not a categorical literary superiority.\n\n| Phase | Combined order |\n| --- | --- |\n'
for p in phases:text+=f'| {p["id"]}: {p["title"]} | {tiers(r["phases"][p["id"]]["candidates"])} |\n'
text+='\n## Evidence and disagreement\n\n'
for p in phases:
 pid=p['id'];v=r['phases'][pid];text+=f'### {pid}: {p["title"]}\n\n'
 for c in v['top']:
  evidence=[]
  for jid,k in keys.items():
   labels={cid:label for label,cid in k['labels'].items()}
   if c not in labels:continue
   review=json.loads((review_dir/f'{jid}.json').read_text());item=next(q for q in review['phases'] if q['phase']==pid)
   pos=next(i for i,tier in enumerate(item['tiers']) if labels[c] in tier)
   ev=next(q for q in item['evidence'] if q['candidate']==labels[c])
   source=B/('outputs-corrected' if r.get('review_set')=='effective-reviews' and c=='kimi-low' else 'outputs')/f'{c}.md'
   st=source.read_text();matches=list(re.finditer(r'^## (P[1-8])[^\n]*$',st,re.M));sections={m[1]:st[m.end():matches[i+1].start() if i+1<len(matches) else len(st)] for i,m in enumerate(matches)}
   if ev['quote'] in sections[pid] and 4<=len(ev['quote'].split())<=18:evidence.append((pos,jid,ev))
  pos,jid,ev=min(evidence,key=lambda x:x[0])
  text+=f'**{names[c]}** ([artifact](outputs/{c}.md)). One supporting reviewer, {names[jid]}, placed it in tier {pos+1}: “{ev["quote"]}” — {ev["reason"]} ([effective review]({review_dir.name}/{jid}.json)).\n\n'
 text+='Leaders after excluding one reviewer model: '+ '; '.join(f'without `{m}`: '+', '.join(names[c] for c in cs) for m,cs in v['leave_one_reviewer_model_out'].items())+'.\n\n'
 text+='Individual reviewer orders:\n\n'
 for jid,k in keys.items():
  raw=v['raw_ranks'][jid];groups={}
  for c,pos in raw:groups.setdefault(pos,[]).append(c)
  order=' > '.join(' = '.join(short[c] for c in cs) for _,cs in sorted(groups.items()))
  text+=f'- {names[jid]}: {order}.\n'
 text+='\n'
text+='## Runtime-note correction\n\nThe original Kimi low completion appended a process note after its complete blurb in response to native max-step handling. The original artifact and all original ranks remain in `outputs/`, `reviews/`, and [original-report.md](original-report.md). A deterministic derivative removes only that separator and process note; no fiction was rewritten or regenerated. Six eligible model/effort conditions reviewed P8 afresh, blind to the correction and prior verdicts; the two Kimi reviewers did not see Kimi outputs in either round and their P8 rankings remain applicable. Final P8 rankings use this corrected comparison. This is a disclosed post-hoc repair, not a preregistered result. [Correction record](blurb-correction.json), [fresh comparisons](reviews-corrected/), and [effective merged reviews](effective-reviews/) preserve provenance.\n\n'
text+='## Effect of increasing effort on this fixture\n\nThe table counts phases in which the higher setting is preferred in a direct comparison, equally weighting the three other reviewer model IDs. Ties are preference ties; eight observations do not establish an effect outside this fixture. The baseline differs across model families.\n\n| Model | Lower setting tested | High preferred | Lower preferred | Tied |\n| --- | --- | ---: | ---: | ---: |\n'
for label,lo,hi in [('GPT-6.1 Sol','sol61-medium','sol61-high'),('GPT-6 Sol','sol6-medium','sol6-high'),('Kimi K3','kimi-low','kimi-high'),('Mistral Large 4','mistral-none','mistral-high')]:
 vals=[v['candidates'][hi]['pairs'][lo]['preference'] for v in r['phases'].values()];text+=f'| {label} | {manifest["conditions"][next(i for i,c in enumerate(manifest["conditions"]) if c["id"]==lo)]["effort"]} | {sum(x>.5 for x in vals)} | {sum(x<.5 for x in vals)} | {sum(abs(x-.5)<1e-9 for x in vals)} |\n'
text+='\n## Objective continuity audit\n\nEvery candidate identified all nine planted errors, so detection count does not select a winner. Mistral high additionally categorized the valid phrase “The inspector” in L10 as a definite POV error; a role noun alone does not establish a shift out of close third. Other samples preserve it or label changes optional. Both Kimi samples offer unsupported motive/speculation wording as one repair option, alongside a sound deletion option. These repair concerns remain visible in [the unblinded director audit](director-audit.json).\n\n'
text+='Word-count diagnostics are in [word-counts.json](word-counts.json). Kimi low exceeds P3. Its original P8 also included a runtime-prompted process note; the blurb itself meets the word target once that tail is removed. Mistral high exceeds P2, P5 and P7. GPT-6 Sol medium slightly exceeds P2. P4 counts include the required state delta and must not be read as narrative-only counts. The word-count method is approximate and does not decide literary merit.\n\n'
val=json.loads((B/'validation.json').read_text());flags=val['evidence_flags']
text+=f'## Verification\n\nAll eight effective reviews parse; each contains P1–P8 and ranks all six eligible candidates exactly once with one evidence item per candidate. Source snapshots, exact-model exclusions, candidate source preservation, and complementary pairwise preferences were checked. Quote checking produced **{len(flags)} flags**; see [validation.json](validation.json) and [the director’s disposition](evidence-disposition.json). A flag identifies a quotation or formatting issue, not an automatic invalidation of a reviewer’s ranking. Raw outputs remain available for inspection.\n\n'
text+='## Method, scope, and limits\n\n'+(B/'report_methods.md').read_text()+'\n'
text+='## Reproduce the analysis\n\nFrom this benchmark directory, run `python3 analyze.py`, `python3 verify_artifacts.py`, then `python3 render_report.py`. These scripts analyze existing artifacts only. `prepare_reviews.py` recreates deterministic reviewer packets and keys from the fixed candidate set; do not regenerate packets mid-review. [run-manifest.json](run-manifest.json), [protocol.md](protocol.md), [protocol-amendments.md](protocol-amendments.md), [candidate-snapshot.json](candidate-snapshot.json), and [blind-keys.json](blind-keys.json) preserve provenance. Reviewer packets expose identities only through the separate key, which was withheld from participants.\n'
correction=B/'effort-control-correction.md'
if correction.exists():
 text=correction.read_text()+'\n---\n\n'+text
 start=text.find('## Effect of increasing effort on this fixture')
 end=text.find('## Objective continuity audit',start)
 if start>=0 and end>=0:text=text[:start]+'## Effort comparisons: correction\n\nKimi/Mistral effort-effect interpretations are withdrawn because effective controls were unverified. Original figures are retained only in the pre-correction report and raw data. See [correction notice](effort-control-correction.md). Sol effort controls were unaffected.\n\n'+text[end:]
(B/'report.md').write_text(text)
print(B/'report.md')
