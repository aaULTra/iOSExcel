#!/usr/bin/env python3
"""Build static bundled dependency closure, preserving load kinds and unknowns."""
import argparse,collections,json,re
from pathlib import Path

def build(app,inventory):
 root=app.resolve();nodes={b['path']:b for b in inventory['binaries']};main='Contents/MacOS/'+inventory['plists']['Contents/Info.plist']['CFBundleExecutable'];main_dir=(root/main).parent
 graph={};unresolved=[]
 for name,b in nodes.items():
  edges=[];loader=(root/name).parent
  def expand(p):return p.replace('@loader_path',str(loader)).replace('@executable_path',str(main_dir))
  rpaths=[expand(p) for p in b.get('rpaths',[])]+[p.replace('@loader_path',str(main_dir)).replace('@executable_path',str(main_dir)) for p in nodes[main].get('rpaths',[])]
  for dep in b.get('dylibs',[]):
   p=dep['path'];target=None
   if p.startswith('@rpath/'):
    candidates=[Path(r)/p[7:] for r in rpaths if not r.startswith('@')]
   elif p.startswith(('@loader_path/','@executable_path/')):candidates=[Path(expand(p))]
   else:candidates=[]
   for c in candidates:
    try:rel=str(c.resolve().relative_to(root))
    except ValueError:continue
    if rel in nodes:target=rel;break
   kind='bundled' if target else 'system' if p.startswith(('/usr/lib/','/System/Library/')) else 'unresolved'
   e={**dep,'target':target,'category':kind};edges.append(e)
   if kind=='unresolved':unresolved.append({'from':name,**e})
  graph[name]=edges
 closure=set();queue=[main]
 while queue:
  n=queue.pop()
  if n in closure:continue
  closure.add(n);queue += [e['target'] for e in graph[n] if e['target']]
 symbols=collections.defaultdict(set);all_symbols=collections.defaultdict(set)
 for n,b in nodes.items():
  for s in b.get('undefined',[]):
   all_symbols[s['library']].add(s['name'])
   if n in closure:symbols[s['library']].add(s['name'])
 appkit=set(s for p,ss in symbols.items() if '/AppKit.framework/' in p for s in ss)
 all_appkit=set(s for p,ss in all_symbols.items() if '/AppKit.framework/' in p for s in ss)
 m=nodes[main]
 return {'main':main,'graph':graph,'startup_closure':sorted(closure),'unresolved':unresolved,'summary':{
  'version':inventory['plists']['Contents/Info.plist'].get('CFBundleShortVersionString'),
  'macho_files':len(nodes),'arm64_files':sum('arm64_error' not in b for b in nodes.values()),'startup_closure_files':len(closure),
  'closure_unresolved_bundled':sum(e['from'] in closure for e in unresolved),
  'closure_appkit_symbols':len(appkit),'all_appkit_symbols':len(all_appkit),
  'closure_appkit_classes':len([s for s in appkit if s.startswith('_OBJC_CLASS_$_')]),
  'main_imports':len(m['undefined']),'main_dylibs':len(m['dylibs']),'main_selectors':len(m['objc_selectors']),
  'main_objc_classes':sum(s['size']//8 for s in m['sections'] if s['name']=='__objc_classlist'),
  'main_objc_protocols':sum(s['size']//8 for s in m['sections'] if s['name']=='__objc_protolist'),
  'main_build':m['build_versions'],'main_arm64_bytes':next(s['size'] for s in m['slices'] if s['cpu']=='0x100000c' and s['subtype']=='0x0'),
  'nib_files':sum(1 for p in app.rglob('*.nib') if p.is_file()),
  'nested_apps':sorted(str(p.relative_to(app)) for p in app.rglob('*.app')),
  'xpc_bundles':sorted(str(p.relative_to(app)) for p in app.rglob('*.xpc')),
  'closure_non_arm64':[n for n in sorted(closure) if 'arm64_error'in nodes[n]]},
  'closure_appkit_symbols':sorted(appkit),'system_imports':{p:sorted(s) for p,s in sorted(symbols.items()) if p.startswith('/')},
  'closure_objc_selectors':sorted({s for n in closure for s in nodes[n].get('objc_selectors',[])})}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('app',type=Path);ap.add_argument('inventory',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();r=build(a.app,json.loads(a.inventory.read_text()));a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['summary'],indent=2))
