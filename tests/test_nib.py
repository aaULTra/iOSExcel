import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from nib_archive import parse,NibError,Reader
from nib_fixture import startup,encode
class NibTest(unittest.TestCase):
 def test_startup_graph(self):
  r=parse(startup());self.assertEqual(len(r['objects']),18);self.assertEqual(r['objects'][2]['class'],'NSCustomObject')
  self.assertEqual(r['objects'][14]['class'],'NSNibOutletConnector')
 def test_all_truncations_fail(self):
  data=startup()
  for n in range(len(data)):
   with self.assertRaises((ValueError,struct.error,UnicodeError)):parse(data[:n])
 def test_invalid_reference(self):
  data=encode([('NSObject',[('ref',10,3)])])
  with self.assertRaises(NibError):parse(data)
 def test_unsupported_version(self):
  data=bytearray(startup());struct.pack_into('<I',data,14,10)
  with self.assertRaises(NibError):parse(data)
 def test_varint_end_marker(self):
  self.assertEqual(Reader(bytes([0x7f,0xff]),0,2).varint(),16383)
  with self.assertRaises(NibError):Reader(b'\x7f'*5,0,5).varint()
 def test_signed_and_float_values(self):
  r=parse(encode([('NSObject',[('i',3,-123),('f',6,1.5),('b',4,True),('nil',9,None)])]))
  values=r['objects'][0]['values'];self.assertEqual(values[0]['value'],-123);self.assertEqual(values[1]['value'],1.5);self.assertIs(values[2]['value'],True);self.assertIsNone(values[3]['value'])
