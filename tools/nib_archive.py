#!/usr/bin/env python3
"""Read-only, bounds-checked NIBArchive v1/coder9 parser.
Format reference: matsmattsson/nibsqueeze/NibArchive.md. No third-party code copied.
This is not a generic NSCoder or a promise that arbitrary macOS nibs work on iOS.
"""
import argparse,hashlib,json,struct
from pathlib import Path

class NibError(ValueError):pass
class Reader:
 def __init__(self,data,start,end):self.data=data;self.pos=start;self.end=end
 def take(self,n):
  if n<0 or self.pos+n>self.end:raise NibError('truncated or overlapping nib table')
  v=self.data[self.pos:self.pos+n];self.pos+=n;return v
 def integer(self,fmt):return struct.unpack('<'+fmt,self.take(struct.calcsize('<'+fmt)))[0]
 def varint(self):
  n=0
  for i in range(5):
   b=self.integer('B')
   if i==4 and b&0x70:raise NibError('nib varint exceeds uint32')
   n|=(b&127)<<(7*i)
   if b&128:return n
  raise NibError('oversized nib varint')
 def done(self):
  if self.pos!=self.end:raise NibError('unexpected bytes between nib tables')

def parse(data):
 if len(data)<50 or data[:10]!=b'NIBArchive':raise NibError('not a NIBArchive')
 version,coder,oc,oo,kc,ko,vc,vo,cc,co=struct.unpack_from('<10I',data,10)
 if (version,coder)!=(1,9):raise NibError('unsupported nib version/coder')
 if not 50==oo<=ko<=vo<=co<=len(data):raise NibError('invalid nib table offsets')
 if max(oc,kc,vc,cc)>1000000:raise NibError('excessive nib table count')
 r=Reader(data,oo,ko);objects=[{'class_index':r.varint(),'value_start':r.varint(),'value_count':r.varint()} for _ in range(oc)];r.done()
 r=Reader(data,ko,vo);keys=[r.take(r.varint()).decode('utf8') for _ in range(kc)];r.done()
 r=Reader(data,vo,co);values=[]
 for _ in range(vc):
  key=r.varint();kind=r.integer('B')
  if kind in (0,1,2,3,6,7):value=r.integer({0:'b',1:'h',2:'i',3:'q',6:'f',7:'d'}[kind])
  elif kind in (4,5):value=kind==4
  elif kind==8:value={'data_hex':r.take(r.varint()).hex()}
  elif kind==9:value=None
  elif kind==10:value={'object':r.integer('I')}
  else:raise NibError('unsupported nib value kind '+str(kind))
  if key>=kc:raise NibError('nib key index out of range')
  if kind==10 and value['object']>=oc:raise NibError('nib object reference out of range')
  values.append({'key':keys[key],'kind':kind,'value':value})
 r.done();r=Reader(data,co,len(data));classes=[]
 for _ in range(cc):
  size=r.varint();extra_count=r.varint();extra=[r.integer('i') for _ in range(extra_count)];name=r.take(size)
  if not name.endswith(b'\0'):raise NibError('unterminated nib class name')
  classes.append({'name':name[:-1].decode('utf8'),'extra':extra})
 r.done()
 for o in objects:
  if o['class_index']>=cc or o['value_start']+o['value_count']>vc:raise NibError('nib object table range invalid')
  o['class']=classes[o['class_index']]['name'];o['values']=values[o['value_start']:o['value_start']+o['value_count']]
 return {'format':version,'coder':coder,'sha256':hashlib.sha256(data).hexdigest(),'objects':objects,'classes':classes,'keys':keys}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('nib',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();r=parse(a.nib.read_bytes());s=json.dumps(r,indent=2,allow_nan=False)+'\n'
 if a.output:a.output.write_text(s)
 else:print(s,end='')
