#!/usr/bin/env python3
"""Check segment audio coverage, ASR word differences and excessive silence.

Run with an interpreter containing faster_whisper. ASR differences require
listening: a transcription error is not automatically an audio error. A clean
ASR result does not prove pronunciation, warmth or full listener review.
"""
import argparse
import difflib
import json
import re
import subprocess
from pathlib import Path


def words(text):
    return re.findall(r"[a-z0-9]+(?:['’][a-z0-9]+)?", text.lower())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('segments',type=Path); p.add_argument('audio',type=Path)
    p.add_argument('--model',default='small.en'); p.add_argument('--out',type=Path,required=True)
    p.add_argument('--pause-threshold',type=float,default=3.0)
    p.add_argument('--beam-size',type=int,default=5)
    p.add_argument('--threads',type=int,default=4)
    p.add_argument('--start',type=int,default=1,help='first segment number to check')
    p.add_argument('--end',type=int,default=0,help='last segment number to check; 0 means the end')
    a=p.parse_args()
    data=json.loads(a.segments.read_text()); rows=[r for r in data['pages'] if r['page']>=a.start and (not a.end or r['page']<=a.end)]
    if not rows: raise SystemExit('no segments in the requested range')
    expected={f"page-{r['page']:02d}.wav" for r in rows}
    actual={p.name for p in a.audio.glob('page-*.wav')}
    missing=expected-actual
    if missing: raise SystemExit(f'missing={sorted(missing)}')
    if a.start == 1 and not a.end and actual != expected:
        raise SystemExit(f'extra={sorted(actual-expected)}')
    from faster_whisper import WhisperModel
    model=WhisperModel(a.model,device='cpu',compute_type='int8',cpu_threads=a.threads)
    result=[]
    for row in rows:
        wav=a.audio / f"page-{row['page']:02d}.wav"
        transcript,info=model.transcribe(str(wav),beam_size=a.beam_size)
        heard=' '.join(x.text.strip() for x in transcript)
        expected_tokens=words(row['text']); heard_tokens=words(heard)
        changes=[]
        for tag,i,j,k,l in difflib.SequenceMatcher(None,expected_tokens,heard_tokens,autojunk=False).get_opcodes():
            if tag!='equal': changes.append({'kind':tag,'expected':expected_tokens[i:j],'transcribed':heard_tokens[k:l]})
        pause=subprocess.run(['ffmpeg','-hide_banner','-i',str(wav),'-af',f'silencedetect=noise=-40dB:d={a.pause_threshold}','-f','null','-'],capture_output=True,text=True)
        durations=[float(x) for x in re.findall(r'silence_duration:\s*([\d.]+)',pause.stderr)]
        seconds=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(wav)],capture_output=True,text=True,check=True).stdout)
        result.append({'page':row['page'],'chapter':row['chapter'],'segment':row['segment'],'seconds':seconds,'transcript':heard,'differences':changes,'silences_seconds':durations,'needs_listen':bool(changes or durations)})
        print(f"{row['page']}: {seconds:.1f}s, {len(changes)} ASR differences, {len(durations)} silence flags",flush=True)
    a.out.write_text(json.dumps({'model':a.model,'segments':result},ensure_ascii=False,indent=2)+'\n')
    flagged=sum(r['needs_listen'] for r in result)
    print(f'{len(result)} checked; {flagged} require listening/adjudication')
    return 1 if flagged else 0

if __name__=='__main__': raise SystemExit(main())
