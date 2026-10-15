import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from objc_startup import Image


def fixture(small=False):
    data = bytearray(0x1000)
    def put(address, fmt, *values):
        struct.pack_into(fmt, data, address - 0x1000, *values)
    def text(address, value):
        data[address-0x1000:address-0x1000+len(value)+1] = value.encode() + b'\0'
    struct.pack_into('<8I', data, 0, 0xfeedfacf, 0x100000c, 0, 2, 1, 152, 0, 0)
    struct.pack_into('<II16sQQQQiiII', data, 32, 0x19, 152, b'__DATA', 0x1000, len(data), 0, len(data), 7, 3, 1, 0)
    struct.pack_into('<16s16sQQIIIIIIII', data, 104, b'__objc_classlist', b'__DATA', 0x1400, 8, 0x400, 3, 0, 0, 0, 0, 0, 0)
    put(0x1400, '<Q', 0x1500)
    put(0x1500, '<5Q', 0x1580, 0, 0, 0, 0x1603)
    put(0x1580, '<5Q', 0x1580, 0, 0, 0, 0x1680)
    put(0x1600, '<4I7Q', 0, 8, 16, 0, 0, 0x1700, 0x1800, 0, 0, 0, 0)
    put(0x1680, '<4I7Q', 1, 8, 40, 0, 0, 0x1700, 0, 0, 0, 0, 0)
    text(0x1700, 'EXSynthetic'); text(0x1720, 'launch:'); text(0x1740, 'v24@0:8@16')
    if small:
        put(0x1800, '<II', 0x8000000c, 1)
        put(0x1808, '<iii', 0x1900-0x1808, 0x1740-0x180c, 0x1a00-0x1810)
        put(0x1900, '<Q', 0x1720)
    else:
        put(0x1800, '<II3Q', 24, 1, 0x1720, 0x1740, 0x1a00)
    return data


class ObjCStartupTest(unittest.TestCase):
    def test_big_and_relative_indirect_methods(self):
        for small in (False, True):
            cls = Image(fixture(small)).selected(['EXSynthetic'])['classes'][0]
            self.assertEqual(cls['instance_start'], 8)
            self.assertEqual(cls['instance_size'], 16)
            self.assertEqual(cls['class_methods'], [])
            self.assertEqual(cls['instance_methods'], [{'selector': 'launch:', 'encoding': 'v24@0:8@16', 'implementation_address': '0x1a00', 'implementation_file_offset': 0xa00}])

    def test_unbacked_method_pointer_fails(self):
        data = fixture()
        struct.pack_into('<Q', data, 0x818, 0xffffffffffffffff)
        with self.assertRaises(ValueError):
            Image(data).selected(['EXSynthetic'])

    def test_unknown_method_flags_fail(self):
        data = fixture()
        struct.pack_into('<I', data, 0x800, 0x40000018)
        with self.assertRaisesRegex(ValueError, 'Unsupported method list'):
            Image(data).selected(['EXSynthetic'])

    def test_missing_class_fails(self):
        with self.assertRaisesRegex(ValueError, 'not found'):
            Image(fixture()).selected(['Absent'])


if __name__ == '__main__':
    unittest.main()
