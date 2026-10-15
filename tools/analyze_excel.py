#!/usr/bin/env python3
import argparse,collections,json,plistlib
from pathlib import Path
from macho import inspect,MAGICS

def analyze(app):
 out={'app':app.name,'directories':{},'plists':{},'binaries':[],'errors':[]}
 for d in ['MacOS','Frameworks','PlugIns','XPCServices','Helpers','Resources','SharedSupport']:
  p=app/'Contents'/d;out['directories'][d]={'exists':p.exists(),'files':sum(x.is_file() for x in p.rglob('*')) if p.exists() else 0}
 for p in sorted(app.rglob('*')):
  if p.is_symlink() or not p.is_file():continue
  rel=str(p.relative_to(app))
  if p.name=='Info.plist':
   try:
    parsed=plistlib.loads(p.read_bytes());keys={'CFBundleExecutable','CFBundleIdentifier','CFBundleShortVersionString','CFBundleVersion','LSMinimumSystemVersion','NSPrincipalClass','NSMainNibFile','NSMainStoryboardFile','LSBackgroundOnly','NSExtension','CFBundlePackageType'}
    out['plists'][rel]={k:v for k,v in parsed.items() if k in keys}
   except Exception as e:out['errors'].append({'path':rel,'error':str(e)})
  with p.open('rb') as f:magic=f.read(4)
  if magic not in MAGICS:continue
  try:r=inspect(p.read_bytes());r['path']=rel;out['binaries'].append(r)
  except Exception as e:out['errors'].append({'path':rel,'error':str(e)})
 return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('app',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 r=analyze(a.app);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,default=str)+'\n')
 print(json.dumps({'binaries':len(r['binaries']),'errors':r['errors'],'output':str(a.output)}))
