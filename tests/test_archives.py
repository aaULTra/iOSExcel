import gzip,io,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from extract_pkg import unpack_cpio,BoundedReader
from macho import arm64
from test_retarget import fixture

def entry(name,data=b'',mode=0o100644):
 n=name.encode()+b'\0'
 fields=[(0,6),(1,6),(mode,6),(0,6),(0,6),(1,6),(0,6),(0,11),(len(n),6),(len(data),11)]
 return b'070707'+b''.join(f'{v:0{w}o}'.encode() for v,w in fields)+n+data
class ArchiveTest(unittest.TestCase):
 def test_extract_regular(self):
  with tempfile.TemporaryDirectory() as t:
   count=unpack_cpio(io.BytesIO(entry('./a/b',b'abc')+entry('TRAILER!!!')),Path(t))
   self.assertEqual(count,1);self.assertEqual((Path(t)/'a/b').read_bytes(),b'abc')
 def test_traversal_rejected(self):
  for name in ['../escape','/absolute']:
   with tempfile.TemporaryDirectory() as t:
    with self.assertRaises(ValueError):unpack_cpio(io.BytesIO(entry(name)),Path(t))
 def test_escaping_symlink_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(ValueError):unpack_cpio(io.BytesIO(entry('link',b'../../outside',0o120777)),Path(t))
 def test_gzip_bounded(self):
  compressed=gzip.compress(b'abc');stream=io.BytesIO(compressed+b'other XAR entry')
  with gzip.GzipFile(fileobj=BoundedReader(stream,len(compressed))) as g:self.assertEqual(g.read(),b'abc')
  self.assertEqual(stream.read(),b'other XAR entry')
 def test_fat64(self):
  thin=fixture();fat=struct.pack('>II',0xcafebabf,1)+struct.pack('>IIQQII',0x100000c,0,40,len(thin),3,0)+thin
  self.assertEqual(arm64(fat),thin)
 def test_fat_cpu_mismatch(self):
  thin=bytearray(fixture());struct.pack_into('<I',thin,4,0x1000007)
  fat=struct.pack('>II',0xcafebabe,1)+struct.pack('>IIIII',0x100000c,0,28,len(thin),2)+thin
  with self.assertRaises(ValueError):arm64(fat)
if __name__=='__main__':unittest.main()
