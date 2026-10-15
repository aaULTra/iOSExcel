#!/usr/bin/env python3
"""Conservative copied-tree Mach-O platform experiment, NOT a working Excel port.
Only explicit path mappings; no engine patches, activation edits, entrypoint edits,
ABI changes, signature bypass or fabricated API stubs. Refuses malformed layouts.
"""
import argparse,hashlib,json,os,shutil,struct,tempfile
from pathlib import Path
from macho import arm64,commands,DYLIBS,MAGICS,inspect,unpack,string

def ver(s):
 v=[int(x) for x in s.split('.')]
 if not 1<=len(v)<=3 or not 0<=v[0]<=65535 or any(not 0<=x<=255 for x in v[1:]):raise ValueError('invalid version')
 v+= [0]*(3-len(v));return v[0]<<16|v[1]<<8|v[2]

def retarget(raw,minos='18.0',sdk='18.0',mapping=None):
 d=bytearray(arm64(raw));cs=commands(d);events=[];seen=0;paths=[]
 for c,o,n in cs:
  if c==0x2c and unpack('<I',d,o+16)[0]:raise ValueError('encrypted image: unsupported')
  if c in (0x24,0x25,0x2f,0x30):raise ValueError('legacy platform command: unsupported')
  if c==0x32:
   pl,mi,sd,nt=unpack('<4I',d,o+8)
   if n!=24+8*nt or pl!=1:raise ValueError('expected macOS LC_BUILD_VERSION')
   struct.pack_into('<3I',d,o+8,2,ver(minos),ver(sdk));seen+=1
   events.append({'offset':o+8,'field':'LC_BUILD_VERSION','before':[pl,mi,sd],'after':[2,ver(minos),ver(sdk)]})
  if c in DYLIBS or c in (0xd,0x8000001c):
   no=unpack('<I',d,o+8)[0]
   if not (12 if c==0x8000001c else 24)<=no<n:raise ValueError('invalid path offset')
   old=string(d,o+no,o+n);new=(mapping or {}).get(old,old)
   if new!=old:
    if '\0' in new:raise ValueError('NUL in replacement')
    b=new.encode()+b'\0'
    if len(b)>n-no:raise ValueError('replacement exceeds load command capacity')
    d[o+no:o+n]=b+b'\0'*(n-no-len(b));events.append({'offset':o+no,'field':'path','before':old,'after':new})
   if c in DYLIBS:paths.append(new)
 if seen!=1:raise ValueError('expected one build version command')
 if len(set(paths))!=len(paths):raise ValueError('duplicate dylib paths require ordinal remapping: unsupported')
 # Validate unchanged file layout and every byte outside explicit modifications.
 commands(d)
 return bytes(d),events

def tree(src,dst,minos,sdk,mapping):
 src=src.resolve();dst=dst.resolve()
 if dst.exists() or dst.is_relative_to(src) or src.is_relative_to(dst):raise ValueError('output must be a new non-overlapping path')
 # Validate ALL inputs before writing anything.
 plan=[]
 for p in sorted(src.rglob('*')):
  if p.is_symlink():
   if not p.resolve().is_relative_to(src):raise ValueError('external source symlink '+str(p))
   continue
  if not p.is_file():continue
  with p.open('rb') as f:magic=f.read(4)
  if magic not in MAGICS:continue
  raw=p.read_bytes();out,events=retarget(raw,minos,sdk,mapping)
  plan.append({'path':str(p.relative_to(src)),'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256(out).hexdigest(),'events':events})
 if not plan:raise ValueError('no Mach-O files')
 dst.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(dir=dst.parent,prefix='.excel-stage-') as tmp:
  stage=Path(tmp)/'app';shutil.copytree(src,stage,symlinks=True)
  for item in plan:
   p=stage/item['path'];raw=p.read_bytes()
   if hashlib.sha256(raw).hexdigest()!=item['input_sha256']:raise ValueError('source changed during copy')
   p.write_bytes(retarget(raw,minos,sdk,mapping)[0])
  stage.rename(dst)
 return {'status':'metadata experiment only; all original code signatures are now stale; re-signing required','binaries':plan}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('destination',type=Path);ap.add_argument('--minos',default='18.0');ap.add_argument('--sdk',default='18.0');ap.add_argument('--map',type=Path);ap.add_argument('--log',required=True,type=Path);a=ap.parse_args()
 try:
  mapping=json.loads(a.map.read_text()) if a.map else {}
  if a.source.is_file():
   if a.destination.exists():raise ValueError('destination already exists')
   raw=a.source.read_bytes();out,events=retarget(raw,a.minos,a.sdk,mapping)
   a.destination.parent.mkdir(parents=True,exist_ok=True)
   with a.destination.open('xb') as f:f.write(out)
   a.destination.chmod(a.source.stat().st_mode & 0o777)
   r={'status':'single-file metadata experiment; signature stale; not runnable','binaries':[{'path':a.source.name,'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256(out).hexdigest(),'events':events}]}
  else:r=tree(a.source,a.destination,a.minos,a.sdk,mapping)
  a.log.parent.mkdir(parents=True,exist_ok=True);a.log.write_text(json.dumps(r,indent=2)+'\n');print('Retargeted',len(r['binaries']),'binaries. Not runnable until compatibility work and re-signing.')
 except (ValueError,OSError,struct.error) as e:ap.exit(1,'FAILED: '+str(e)+'\n')
