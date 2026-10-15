import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from excel_retarget import rewrite_load_paths, retarget, verify_changes
from macho import commands, inspect


def dylib(name, command=0xc):
    data = name.encode() + b'\0'
    size = (24 + len(data) + 7) & ~7
    return struct.pack('<6I', command, size, 24, 0, 0x2d0000, 0x2d0000) + data + b'\0'*(size-24-len(data))


def fixture():
    cmds = struct.pack('<6I', 0x32, 24, 1, 0xb0000, 0xc0000, 0)
    cmds += dylib('/long/original/AppKit') + dylib('/long/original/Cocoa', 0x80000018)
    return struct.pack('<8I', 0xfeedfacf, 0x100000c, 0, 2, 3, len(cmds), 0, 0) + cmds + b'unmodified-payload'


class LoaderPathTest(unittest.TestCase):
    def test_distinct_facades_retain_command_order_kind_and_payload(self):
        old = fixture()
        mapping = {'/long/original/AppKit': '@rpath/A', '/long/original/Cocoa': '@rpath/C'}
        new, events = rewrite_load_paths(old, mapping)
        self.assertEqual([(c, o, n) for c, o, n in commands(old)], commands(new))
        self.assertEqual(inspect(new)['dylibs'], [{'kind': 'load', 'path': '@rpath/A'}, {'kind': 'weak', 'path': '@rpath/C'}])
        self.assertEqual(old[-18:], new[-18:])
        self.assertEqual(inspect(new)['build_versions'][0]['platform'], 1)
        self.assertEqual(len(events), 2)
        self.assertTrue(all(e['length'] > 0 for e in events))
        ios, _ = retarget(old, mapping=mapping)
        self.assertEqual(inspect(ios)['build_versions'][0]['platform'], 2)
        self.assertEqual(inspect(ios)['dylibs'], inspect(new)['dylibs'])

    def test_collapsing_ordinals_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'duplicate dylib'):
            rewrite_load_paths(fixture(), {'/long/original/AppKit': '@rpath/One', '/long/original/Cocoa': '@rpath/One'})

    def test_invalid_mapping_fails(self):
        for value in ['', 'bad\0path', 'x'*200]:
            with self.assertRaises(ValueError):
                rewrite_load_paths(fixture(), {'/long/original/AppKit': value})
        for mapping in [[], {'/long/original/AppKit': None}]:
            with self.assertRaises(ValueError):
                retarget(fixture(), mapping=mapping)

    def test_unlogged_mutation_fails(self):
        old = fixture()
        changed = old[:-1] + bytes([old[-1] ^ 1])
        with self.assertRaisesRegex(ValueError, 'outside logged fields'):
            verify_changes(old, changed, [])


if __name__ == '__main__':
    unittest.main()
