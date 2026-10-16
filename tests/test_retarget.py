import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from excel_retarget import retarget
from macho import commands

def fixture(extra=b''):
 cmd=struct.pack('<6I',0x32,24,1,0xb0000,0xc0000,0)+extra
 n=1+(1 if extra else 0)
 return struct.pack('<8I',0xfeedfacf,0x100000c,0,2,n,len(cmd),0,0)+cmd+b'untouched-arm64-code'
class RetargetTest(unittest.TestCase):
 def test_metadata_only(self):
  old=fixture();new,log=retarget(old)
  self.assertEqual(new[56:],old[56:]);self.assertEqual(struct.unpack_from('<I',new,40)[0],2)
  self.assertEqual(new[:40],old[:40]);self.assertEqual(new[52:],old[52:]);self.assertEqual(len(log),1)
 def test_simulator_is_explicit(self):
  old=fixture();new,log=retarget(old,platform=7)
  self.assertEqual(struct.unpack_from('<I',new,40)[0],7)
  self.assertEqual(new[56:],old[56:])
  self.assertEqual(log[0]['after'][0],7)
  with self.assertRaises(ValueError):retarget(old,platform=6)
 def test_truncated(self):
  for n in range(56):
   with self.assertRaises((ValueError,struct.error)):retarget(fixture()[:n])
 def test_reject_ios(self):
  d=bytearray(fixture());struct.pack_into('<I',d,40,2)
  with self.assertRaises(ValueError):retarget(d)
 def test_reject_oversize_mapping(self):
  name=b'/AppKit\0';cmd=struct.pack('<6I',0xc,32,24,0,0,0)+name
  with self.assertRaises(ValueError):retarget(fixture(cmd),mapping={'/AppKit':'x'*100})
 def test_reject_bad_command_size(self):
  d=bytearray(fixture());struct.pack_into('<I',d,36,4)
  with self.assertRaises(ValueError):retarget(d)
if __name__=='__main__':unittest.main()
