#!/usr/bin/env python3
"""Extract gzip cpio payloads without executing installer scripts (Linux/macOS).
Supports the odc/newc payloads used by the inspected Microsoft Excel packages.
Rejects traversal, special files, duplicate files and escaping symlinks.
"""
import argparse,gzip,hashlib,json,os,shutil,stat,struct,zlib
from pathlib import Path,PurePosixPath
import xml.etree.ElementTree as ET

def exact(f,n):
 b=f.read(n)
 if len(b)!=n: raise ValueError('truncated archive')
 return b

def toc(f):
 magic,hs,version,cs,us,alg=struct.unpack('>IHHQQI',exact(f,28))
 if magic!=0x78617221 or version!=1 or cs>32*1024*1024 or us>128*1024*1024: raise ValueError('unsupported XAR')
 f.seek(hs); xml=zlib.decompress(exact(f,cs))
 if len(xml)!=us: raise ValueError('XAR TOC size mismatch')
 r=ET.fromstring(xml); out=[]
 def walk(e,p=''):
  for x in e.findall('file'):
   n=p+'/'+x.findtext('name'); d=x.find('data')
   if d is not None: out.append((n,hs+cs+int(d.findtext('offset')),int(d.findtext('length')),d.find('encoding').get('style')))
   walk(x,n)
 walk(r.find('toc')); return out

def unpack_cpio(f,dest):
 dest=dest.resolve(); count=0
 while True:
  magic=exact(f,6)
  if magic==b'070707':
   h=exact(f,70);mode=int(h[12:18],8);namesize=int(h[53:59],8);size=int(h[59:70],8);align=1;hdr=76
  elif magic in (b'070701',b'070702'):
   h=exact(f,104);v=[int(h[i:i+8],16) for i in range(0,104,8)];mode=v[1];size=v[6];namesize=v[11];align=4;hdr=110
  else: raise ValueError('unsupported cpio magic '+repr(magic))
  if not 0<namesize<32768:raise ValueError('invalid cpio path size')
  raw=exact(f,namesize)
  if raw[-1:]!=b'\0':raise ValueError('unterminated path')
  name=raw[:-1].decode('utf8');exact(f,(-(hdr+namesize))%align)
  if name=='TRAILER!!!':break
  rel=PurePosixPath(name)
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('unsafe archive path')
  p=dest/rel
  if not p.resolve().is_relative_to(dest):raise ValueError('symlink escape')
  p.parent.mkdir(parents=True,exist_ok=True)
  if stat.S_ISDIR(mode):p.mkdir(exist_ok=True)
  elif stat.S_ISLNK(mode):
   target=exact(f,size).decode('utf8')
   if Path(target).is_absolute() or not (p.parent/target).resolve().is_relative_to(dest):raise ValueError('escaping symlink')
   p.symlink_to(target)
  elif stat.S_ISREG(mode):
   with p.open('xb') as o:
    remaining=size
    while remaining:
     b=exact(f,min(1024*1024,remaining));o.write(b);remaining-=len(b)
   p.chmod(mode&0o777)
  else:raise ValueError('unsupported special file '+name)
  exact(f,(-size)%align);count+=1
 return count

class BoundedReader:
 def __init__(self,f,size):self.f=f;self.remaining=size
 def read(self,n=-1):
  if n<0:n=self.remaining
  b=self.f.read(min(n,self.remaining));self.remaining-=len(b);return b

def main():
 ap=argparse.ArgumentParser();ap.add_argument('package',type=Path);ap.add_argument('destination',type=Path);a=ap.parse_args()
 if a.destination.exists():ap.error('destination must not exist')
 with a.package.open('rb') as f:
  entries=toc(f); payloads=[e for e in entries if e[0].endswith('/Payload')]
  if len(payloads)!=1:ap.error('expected one payload; supply the single Excel updater package')
  name,offset,size,enc=payloads[0]
  if offset+size>a.package.stat().st_size:raise ValueError('incomplete package')
  f.seek(offset)
  if exact(f,2)!=b'\x1f\x8b':raise ValueError('only gzip cpio supported; use pkgutil on macOS for other formats')
  f.seek(offset);a.destination.mkdir(parents=True)
  with gzip.GzipFile(fileobj=BoundedReader(f,size)) as g:
   count=unpack_cpio(g,a.destination)
   while g.read(1024*1024):pass  # Validate gzip trailer/CRC, bounded to this payload.
 print(json.dumps({'payload':name,'entries':count,'destination':str(a.destination)}))
if __name__=='__main__':main()
