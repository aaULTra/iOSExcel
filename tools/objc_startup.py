#!/usr/bin/env python3
"""Read selected on-disk ObjC class/method contracts; never loads the executable.

Limited to plain arm64, unchained pointers and Apple's big/indirect-small method
lists. Shared-cache/direct-selector and unfamiliar representations fail closed.
Layout reference: apple-oss-distributions/objc4, objc4-841.13,
runtime/objc-runtime-new.h (class_ro_t, method_t, method_list_t).
"""
import argparse
import json
from pathlib import Path
from macho import arm64, commands, unpack, string


class Image:
    def __init__(self, raw):
        self.data = arm64(raw)
        self.sections = []
        self.ranges = []
        for cmd, offset, size in commands(self.data):
            if cmd == 0x80000034:
                raise ValueError('Chained fixup pointers are not supported by this inspector')
            if cmd != 0x19:
                continue
            vm, _, fileoff, filesize = unpack('<4Q', self.data, offset + 24)
            if fileoff + filesize > len(self.data):
                raise ValueError('Segment exceeds file')
            if filesize:
                self.ranges.append((vm, filesize, fileoff))
            count = unpack('<I', self.data, offset + 64)[0]
            if 72 + count * 80 != size:
                raise ValueError('Invalid section count')
            for i in range(count):
                q = offset + 72 + i * 80
                name = self.data[q:q+16].split(b'\0', 1)[0].decode('ascii')
                address, length = unpack('<QQ', self.data, q + 32)
                self.sections.append((name, address, length))

    def offset(self, address, length=1):
        for vm, size, off in self.ranges:
            if vm <= address and length <= size - (address - vm):
                return off + address - vm
        raise ValueError(f'Address {address:#x} is not file-backed')

    def read(self, fmt, address):
        import struct
        return unpack(fmt, self.data, self.offset(address, struct.calcsize(fmt)))

    def text(self, address):
        off = self.offset(address)
        end = next(off + size - (address - vm) for vm, size, _ in self.ranges if vm <= address < vm + size)
        return string(self.data, off, end)

    def methods(self, address):
        if not address:
            return []
        flags, count = self.read('<II', address)
        if flags & 0x7fff0000 or count > 100000:
            raise ValueError('Unsupported method list flags/count')
        small = bool(flags & 0x80000000)
        size = flags & 0xfffc
        if size != (12 if small else 24):
            raise ValueError('Unexpected method entry size')
        self.offset(address, 8 + count * size)
        result = []
        for i in range(count):
            entry = address + 8 + i * size
            if small:
                name, types, imp = self.read('<iii', entry)
                name = self.read('<Q', entry + name)[0]
                types += entry + 4
                imp += entry + 8
            else:
                name, types, imp = self.read('<QQQ', entry)
            self.offset(imp, 4)
            result.append({'selector': self.text(name), 'encoding': self.text(types),
                           'implementation_address': hex(imp), 'implementation_file_offset': self.offset(imp)})
        return result

    def record(self, address, include_meta=True):
        isa, superclass, _, _, bits = self.read('<5Q', address)
        # Plain arm64 on-disk ro pointer, excluding the three ObjC data flags.
        ro = bits & ~7
        flags, start, size, reserved = self.read('<4I', ro)
        if reserved:
            raise ValueError('Unexpected class_ro reserved field')
        name, methods = self.read('<QQ', ro + 24)
        result = {'name': self.text(name), 'class_address': hex(address),
                  'superclass_pointer_before_binding': hex(superclass), 'ro_flags': hex(flags),
                  'instance_start': start, 'instance_size': size, 'instance_methods': self.methods(methods)}
        if include_meta:
            result['class_methods'] = self.record(isa, False)['instance_methods']
        return result

    def selected(self, names):
        found = []
        for name, address, size in self.sections:
            if name != '__objc_classlist':
                continue
            if size % 8:
                raise ValueError('Misaligned class list')
            for i in range(size // 8):
                pointer = self.read('<Q', address + 8*i)[0]
                bits = self.read('<Q', pointer + 32)[0]
                cname = self.text(self.read('<Q', (bits & ~7) + 24)[0])
                if cname in names:
                    found.append(self.record(pointer))
        missing = sorted(set(names) - {x['name'] for x in found})
        if missing:
            raise ValueError('Requested classes not found: ' + ', '.join(missing))
        return {'kind': 'Static Objective-C method metadata; no application execution', 'classes': found}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('binary', type=Path)
    ap.add_argument('--class', dest='classes', action='append', required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result = Image(args.binary.read_bytes()).selected(args.classes)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Read static method contracts for ' + ', '.join(c['name'] for c in result['classes']))


if __name__ == '__main__':
    main()
