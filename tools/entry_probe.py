#!/usr/bin/env python3
"""Identify arm64 LC_MAIN's first direct branch and its imported stub, if any.
Read-only, stdlib only. Does not infer where neighboring functions start/end.
"""
import argparse,json
from pathlib import Path
from macho import arm64,commands,unpack,string

def probe(raw):
 d=arm64(raw);cs=commands(d);sym=next(o for c,o,n in cs if c==2);so,ct,st,ss=unpack('<4I',d,sym+8)
 dy=next(o for c,o,n in cs if c==0xb);indoff,indn=unpack('<II',d,dy+56);stubmap={};sections=[]
 for c,o,n in cs:
  if c!=0x19:continue
  for i in range(unpack('<I',d,o+64)[0]):
   q=o+72+80*i;addr,size,off=unpack('<QQI',d,q+32);sections.append((addr,size,off));flags,r1,r2=unpack('<III',d,q+64)
   if flags&0xff==8:
    if not r2 or r1+size//r2>indn:raise ValueError('invalid stub indirect range')
    for j in range(size//r2):
     idx=unpack('<I',d,indoff+4*(r1+j))[0]
     if idx&0xc0000000:continue
     if idx>=ct:raise ValueError('invalid stub symbol index')
     si=unpack('<I',d,so+idx*16)[0];stubmap[addr+j*r2]=string(d,st+si,st+ss)
 entry=next(unpack('<Q',d,o+8)[0] for c,o,n in cs if c==0x80000028)
 addr=next(a+entry-o for a,n,o in sections if o<=entry<o+n);word=unpack('<I',d,entry)[0]
 r={'entry_file_offset':entry,'entry_address':hex(addr),'instruction':hex(word),'kind':'unrecognized; further disassembly required'}
 if word&0x7c000000==0x14000000:
  imm=word&0x3ffffff;imm-=1<<26 if imm&(1<<25) else 0;target=addr+imm*4
  r.update(kind='BL' if word&0x80000000 else 'B (tail branch)',target=hex(target),imported_symbol=stubmap.get(target))
 return r
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('binary',type=Path);a=ap.parse_args();print(json.dumps(probe(a.binary.read_bytes()),indent=2))
