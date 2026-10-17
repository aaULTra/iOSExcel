import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from macho_bindings import decode_stream, classic_bindings, leb
from excel_retarget import weaken_unused_loads, verify_changes
from macho import inspect


def image(binding=b'', imported=False, flags=0x80):
    name=b'/Optional\0'
    size=(24+len(name)+7)&~7
    library=struct.pack('<6I',0xc,size,24,0,0x10000,0x10000)+name+b'\0'*(size-24-len(name))
    command_size=len(library)+24+48
    payload_start=32+command_size
    symbol=struct.pack('<IBBHQ',1,1,0,0x100,0) if imported else b''
    strings=b'\0_Required\0' if imported else b'\0'
    symoff=payload_start+len(binding)
    symtab=struct.pack('<6I',2,24,symoff,int(imported),symoff+len(symbol),len(strings))
    info=struct.pack('<12I',0x80000022,48,0,0,payload_start if binding else 0,len(binding),0,0,0,0,0,0)
    header=struct.pack('<8I',0xfeedfacf,0x100000c,0,2,3,command_size,flags,0)
    return header+library+symtab+info+binding+symbol+strings+b'UNCHANGED_MACHINE_CODE'


class ClassicBindingTests(unittest.TestCase):
    def test_library_usage_and_repeat_count(self):
        data=b'\x20\x80\x01\x40_name\0\x51\x60\x7e\x70\x00\xc0\x07\x08\x00'
        self.assertEqual(decode_stream(data),[{'ordinal':128,'symbol':'_name','count':7}])

    def test_lazy_program_boundaries_and_weak_lookup(self):
        data=b'\x11\x40_a\0\x90\x00\x12\x40_b\0\x90\x00'
        self.assertEqual([r['ordinal'] for r in decode_stream(data,lazy=True)],[1,2])
        self.assertEqual(decode_stream(b'\x40_a\0\x90\x00',weak=True)[0]['ordinal'],-3)

    def test_malformed_and_unknown_streams_fail(self):
        for data in [b'\x20\x80',b'\x40_unterminated',b'\xd0',b'\x31',b'\x50',b'\x00\x90',b'\x91',b'\x42_name\0',b'\x90']:
            with self.subTest(data=data), self.assertRaises(ValueError): decode_stream(data)
        with self.assertRaises(ValueError): leb(b'\xff'*10,0)

    def test_exact_binary_library_attribution(self):
        records=classic_bindings(image(b'\x11\x40_call\0\x70\x00\x90\0'))
        self.assertEqual(records[0]['library'],'/Optional')
        self.assertEqual(records[0]['symbol'],'_call')

    def test_unused_load_changes_only_its_four_byte_kind(self):
        original=image()
        changed,events=weaken_unused_loads(original,{'/Optional'})
        self.assertEqual(len(events),1)
        self.assertEqual((events[0]['offset'],events[0]['length']),(32,4))
        verify_changes(original,changed,events)
        self.assertEqual(original[36:],changed[36:])
        self.assertEqual(inspect(changed)['dylibs'],[{'kind':'weak','path':'/Optional'}])

    def test_either_symbol_or_binding_use_forbids_weakening(self):
        cases=[image(imported=True), image(b'\x11\x40_call\0\x70\x00\x90\0')]
        for original in cases:
            with self.assertRaisesRegex(ValueError,'still has'): weaken_unused_loads(original,{'/Optional'})

    def test_flat_namespace_and_unknown_binding_format_forbid_weakening(self):
        for original in [image(flags=0),image(flags=0x180),image(b'\x3e\x40_dynamic\0\x90\0'),image(b'\xd0')]:
            with self.assertRaises(ValueError):weaken_unused_loads(original,{'/Optional'})

    def test_binding_range_and_ordinal_checks(self):
        with self.assertRaisesRegex(ValueError,'ordinal outside'):
            classic_bindings(image(b'\x12\x40_bad\0\x90\0'))
        original=bytearray(image(b'\x11\x40_bad\0\x90\0'))
        # dylib command is 40 bytes; dyld_info follows its 24-byte symbol command.
        info=32+40+24
        struct.pack_into('<I',original,info+16,1)
        with self.assertRaisesRegex(ValueError,'outside payload'):classic_bindings(original)


if __name__=='__main__':unittest.main()
