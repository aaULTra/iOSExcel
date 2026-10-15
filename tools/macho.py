"""Bounds-checked read-only Mach-O inventory; no vendor-specific offsets."""
import hashlib,struct,plistlib
ARM64=0x100000c
DYLIBS={0xc:'load',0x80000018:'weak',0x8000001f:'reexport',0x80000023:'upward'}
MAGICS={b'\xcf\xfa\xed\xfe',b'\xce\xfa\xed\xfe',b'\xca\xfe\xba\xbe',b'\xca\xfe\xba\xbf',b'\xbe\xba\xfe\xca',b'\xbf\xba\xfe\xca'}
def unpack(fmt,d,o):
 if o<0 or o+struct.calcsize(fmt)>len(d):raise ValueError('out-of-bounds Mach-O record')
 return struct.unpack_from(fmt,d,o)
def string(d,o,end):
 if not 0<=o<end<=len(d):raise ValueError('invalid string range')
 n=d.find(b'\0',o,end)
 if n<0:raise ValueError('unterminated Mach-O string')
 return bytes(d[o:n]).decode('utf8','replace')
def slices(d):
 magic=bytes(d[:4]);out=[]
 if magic in (b'\xca\xfe\xba\xbe',b'\xca\xfe\xba\xbf',b'\xbe\xba\xfe\xca',b'\xbf\xba\xfe\xca'):
  endian='>' if magic[0]==0xca else '<';fat64=magic in (b'\xca\xfe\xba\xbf',b'\xbf\xba\xfe\xca');n=unpack(endian+'I',d,4)[0]
  if n>64:raise ValueError('too many fat slices')
  for i in range(n):
   rec=unpack(endian+('IIQQII' if fat64 else 'IIIII'),d,8+i*(32 if fat64 else 20));cpu,sub,off,size=rec[:4]
   if off+size>len(d) or off<8+n*(32 if fat64 else 20):raise ValueError('invalid fat slice range')
   out.append((cpu,sub,off,size))
 else:
  cpu,sub=unpack('<II',d,4);out=[(cpu,sub,0,len(d))]
 return out

def arm64(d):
 matches=[x for x in slices(d) if x[0]==ARM64 and x[1]&0xffffff==0]
 if len(matches)!=1:raise ValueError('expected exactly one plain arm64 slice')
 _,_,o,n=matches[0];out=bytes(d[o:o+n])
 if unpack('<II',out,4)!=(ARM64,0):raise ValueError('fat slice/header CPU mismatch')
 return out
def commands(d):
 magic,cpu,sub,ft,n,sz,flags,res=unpack('<8I',d,0)
 if magic!=0xfeedfacf:raise ValueError('not little-endian Mach-O 64')
 if n>100000 or 32+sz>len(d):raise ValueError('invalid load command area')
 o=32;out=[]
 for _ in range(n):
  c,s=unpack('<II',d,o)
  if s<8 or s%8 or o+s>32+sz:raise ValueError('invalid command size')
  minimum={0x19:72,2:24,0xb:80,0x32:24,0x2c:24,0x1d:16,0xc:24,0xd:24,0x80000018:24,0x8000001f:24,0x80000023:24,0x8000001c:12,0x80000028:24}.get(c,8)
  if s<minimum:raise ValueError('undersized known load command')
  out.append((c,o,s));o+=s
 if o!=32+sz:raise ValueError('load command size mismatch')
 return out

def version(v):return '.'.join(str(x) for x in (v>>16,(v>>8)&255,v&255))
def inspect(d):
 result={'sha256':hashlib.sha256(d).hexdigest(),'slices':[{'cpu':hex(c),'subtype':hex(s),'offset':o,'size':n} for c,s,o,n in slices(d)]}
 try:t=arm64(d)
 except ValueError as e:result['arm64_error']=str(e);return result
 cs=commands(t);result.update(filetype=unpack('<I',t,12)[0],dylibs=[],rpaths=[],sections=[],undefined=[],objc_classes=[],objc_selectors=[],build_versions=[])
 libraries=[]
 for c,o,n in cs:
  if c in DYLIBS or c in (0xd,0x8000001c):
   no=unpack('<I',t,o+8)[0]
   if no<(12 if c==0x8000001c else 24):raise ValueError('bad dylib/rpath name offset')
   name=string(t,o+no,o+n)
   if c in DYLIBS:result['dylibs'].append({'kind':DYLIBS[c],'path':name});libraries.append(name)
   elif c==0xd:result['install_name']=name
   else:result['rpaths'].append(name)
  elif c==0x32:
   platform,mi,sdk,nt=unpack('<4I',t,o+8)
   if 24+8*nt!=n:raise ValueError('bad build version tool array')
   result['build_versions'].append({'platform':platform,'minos':version(mi),'sdk':version(sdk)})
  elif c in (0x24,0x25):result['legacy_version']={'command':hex(c),'minos':version(unpack('<I',t,o+8)[0])}
  elif c==0x80000028:result['entryoff']=unpack('<Q',t,o+8)[0]
  elif c==0x1d:
   off,size=unpack('<II',t,o+8)
   if off+size>len(t):raise ValueError('signature outside file')
   if size>=12:
    magic,length,count=unpack('>III',t,off)
    if magic==0xfade0cc0:
     if length>size or 12+8*count>length:raise ValueError('bad code signature superblob')
     for i in range(count):
      slot,rel=unpack('>II',t,off+12+8*i)
      if rel+8>length:raise ValueError('bad signature blob offset')
      bm,bl=unpack('>II',t,off+rel)
      if rel+bl>length:raise ValueError('bad signature blob length')
      if bm==0xfade7171:result['original_entitlements']=plistlib.loads(t[off+rel+8:off+rel+bl])
  elif c==0x2c:result['encrypted']=bool(unpack('<I',t,o+16)[0])
  elif c==0x19:
   ns=unpack('<I',t,o+64)[0]
   if 72+80*ns!=n:raise ValueError('bad section count')
   for i in range(ns):
    p=o+72+80*i;sn=t[p:p+16].split(b'\0',1)[0].decode();seg=t[p+16:p+32].split(b'\0',1)[0].decode();addr,size,off=unpack('<QQI',t,p+32)
    result['sections'].append({'segment':seg,'name':sn,'address':addr,'size':size,'offset':off})
    if sn in ('__objc_methname','__objc_classname'):
     if off+size>len(t):raise ValueError('section outside file')
     key='objc_selectors' if sn=='__objc_methname' else 'objc_classes'
     result[key]=sorted(set(x.decode('utf8','replace') for x in t[off:off+size].split(b'\0') if x))
 for c,o,n in cs:
  if c!=2:continue
  sy,ct,st,ss=unpack('<4I',t,o+8)
  if sy+ct*16>len(t) or st+ss>len(t):raise ValueError('symbol table outside file')
  for i in range(ct):
   idx,typ,sect,desc,value=unpack('<IBBHQ',t,sy+16*i)
   if typ&0xe0 or typ&0x0e or not idx:continue
   name=string(t,st+idx,st+ss);ord=desc>>8
   result['undefined'].append({'name':name,'ordinal':ord,'library':libraries[ord-1] if 0<ord<=len(libraries) else 'special:'+str(ord),'weak':bool(desc&0x40)})
 return result
