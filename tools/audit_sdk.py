#!/usr/bin/env python3
"""Conservative iPhoneOS .tbd declaration audit; never claims runtime ABI compatibility.
Requires PyYAML. Unknown stub formats/reexports remain explicitly unresolved.
"""
import argparse,json,re
from pathlib import Path
import yaml
class Loader(yaml.SafeLoader):pass
Loader.add_multi_constructor('!',lambda loader,tag,node:loader.construct_mapping(node,deep=True))

def ios_arm64(group,parent=None):
 g=group if 'targets' in group or 'archs' in group else parent or group
 if 'targets'in g:return any(t.startswith('arm64-ios') and 'simulator' not in t and 'macabi' not in t for t in g['targets'])
 return g.get('platform','').lower() in ('ios','iphoneos') and 'arm64' in g.get('archs',[])

def audit(sdk,dependencies):
 cache={};active=set()
 def exports(install):
  install=re.sub(r'/Versions/[^/]+','',install)
  if install in cache:return cache[install]
  if install in active:return set(),['cyclic reexport '+install]
  active.add(install);path=sdk/install.lstrip('/')
  path=path.with_suffix('.tbd') if path.suffix=='.dylib' else Path(str(path)+'.tbd')
  symbols=set();unknown=[]
  if not path.is_file():unknown.append('SDK stub absent: '+install)
  else:
   try:
    docs=list(yaml.load_all(path.read_text(),Loader=Loader))
    if not docs or any(not isinstance(d,dict) or 'install-name' not in d for d in docs):raise ValueError('unsupported stub schema')
    for doc in docs:
     if not ios_arm64(doc):continue
     for key in ['exports','reexports']:
      for g in doc.get(key,[]):
       if not ios_arm64(g,doc):continue
       for k in ['symbols','weak-symbols','weak-def-symbols','thread-local-symbols']:symbols.update(g.get(k,[]))
       for n in g.get('objc-classes',[]):symbols.update(['_OBJC_CLASS_$_'+n,'_OBJC_METACLASS_$_'+n])
       symbols.update('_OBJC_IVAR_$_'+n for n in g.get('objc-ivars',[]))
       symbols.update('_OBJC_EHTYPE_$_'+n for n in g.get('objc-eh-types',[]))
       for lib in g.get('re-exports',[]):
        ss,uu=exports(lib);symbols.update(ss);unknown.extend(uu)
     for g in doc.get('reexported-libraries',[]):
      if ios_arm64(g,doc):
       for lib in g.get('libraries',[]):
        ss,uu=exports(lib);symbols.update(ss);unknown.extend(uu)
    if not any(ios_arm64(d) for d in docs):unknown.append('No arm64 iOS declaration: '+install)
   except (ValueError,yaml.YAMLError,TypeError) as e:unknown.append('Stub parse unresolved '+install+': '+str(e))
  active.remove(install);cache[install]=(symbols,unknown);return symbols,unknown
 rows=[]
 for lib,required in dependencies['system_imports'].items():
  found,unknown=exports(lib);missing=sorted(set(required)-found)
  rows.append({'macos_install_name':lib,'required_symbol_count':len(required),'declared_count':len(set(required)&found),'not_found_in_parsed_exports':missing,'unresolved':sorted(set(unknown))})
 return {'status':'SDK declaration audit only, NOT runtime compatibility or a complete dyld closure proof','sdk':str(sdk),'libraries':rows}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('dependencies',type=Path);ap.add_argument('sdk',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
 if not (a.sdk/'System/Library/Frameworks/UIKit.framework').exists():ap.error('expected an actual iPhoneOS SDK')
 a.output.write_text(json.dumps(audit(a.sdk,json.loads(a.dependencies.read_text())),indent=2)+'\n')
