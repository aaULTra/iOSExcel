"""Synthetic NIBArchive resources authored for this project's tests; no vendor data."""
import struct
from pathlib import Path

def varint(value):
 out=bytearray()
 while True:
  b=value&127;value>>=7;out.append(b|(0 if value else 128))
  if not value:return bytes(out)
def encode(objects):
 classes=list(dict.fromkeys(c for c,fields in objects));keys=list(dict.fromkeys(k for c,fields in objects for k,t,v in fields));vals=[];obj=bytearray()
 for cls,fields in objects:
  obj+=varint(classes.index(cls))+varint(len(vals))+varint(len(fields));vals.extend(fields)
 key_data=b''.join(varint(len(k.encode()))+k.encode() for k in keys);value_data=bytearray()
 for key,kind,value in vals:
  value_data+=varint(keys.index(key))+bytes([kind])
  if kind in (0,1,2,3,6,7,10):value_data+=struct.pack('<'+{0:'b',1:'h',2:'i',3:'q',6:'f',7:'d',10:'I'}[kind],value)
  elif kind==8:value_data+=varint(len(value))+value
  elif kind not in (4,5,9):raise ValueError('bad synthetic kind')
 class_data=b''.join(varint(len(c.encode())+1)+varint(0)+c.encode()+b'\0' for c in classes)
 oo=50;ko=oo+len(obj);vo=ko+len(key_data);co=vo+len(value_data)
 return b'NIBArchive'+struct.pack('<10I',1,9,len(objects),oo,len(keys),ko,len(vals),vo,len(classes),co)+obj+key_data+value_data+class_data

def startup():
 R=lambda key,index:(key,10,index)
 S=lambda value:('NSString',[('NS.bytes',8,value.encode())])
 A=lambda *refs:('NSArray',[('NSInlinedValue',5,False)]+[R('UINibEncoderEmptyKey',r) for r in refs])
 return encode([
  ('NSObject',[R('IB.objectdata',1)]),
  ('NSIBObjectData',[R('NSRoot',2),R('NSObjectsKeys',3),R('NSConnections',8),R('NSVisibleWindows',9),R('NSAccessibilityConnectors',10)]),
  ('NSCustomObject',[R('NSClassName',4)]),
  A(6,7,11,12),
  S('EXTestApplication'),S('EXTestDelegate'),
  ('NSCustomObject',[R('NSClassName',5)]),
  ('NSCustomObject',[R('NSClassName',13)]),
  ('NSMutableArray',[('NSInlinedValue',5,False),R('UINibEncoderEmptyKey',14)]),
  ('NSMutableSet',[('NSInlinedValue',5,False)]),
  ('NSMutableArray',[('NSInlinedValue',5,False)]),
  ('NSCustomObject',[R('NSClassName',15)]),
  ('NSCustomObject',[R('NSClassName',16)]),S('EXTestDocumentController'),
  ('NSNibOutletConnector',[R('NSSource',2),R('NSDestination',6),R('NSLabel',17)]),
  S('NSFontManager'),S('NSApplication'),S('delegate')])
if __name__=='__main__':
 import sys,plistlib
 contents=Path(sys.argv[1]);(contents/'Resources/Base.lproj').mkdir(parents=True,exist_ok=True)
 (contents/'Resources/Base.lproj/Main.nib').write_bytes(startup())
 (contents/'Info.plist').write_bytes(plistlib.dumps({'NSPrincipalClass':'EXTestApplication','NSMainNibFile':'Main'}))
