"""Checked classic dyld binding usage, not a general-purpose dyld interpreter.
Threaded/chained formats are refused. No bind bytes are ever modified.
Opcode definitions: Apple XNU EXTERNAL_HEADERS/mach-o/loader.h.
"""
from macho import arm64, commands, DYLIBS, unpack, string


def leb(data, offset, signed=False):
    value = shift = 0
    for _ in range(10):
        if offset >= len(data):
            raise ValueError('Truncated binding LEB128')
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7f) << shift
        shift += 7
        if not byte & 0x80:
            if signed and byte & 0x40:
                value -= 1 << shift
            if not (-(1 << 63) <= value < (1 << 63) if signed else 0 <= value < (1 << 64)):
                raise ValueError('Binding LEB128 overflow')
            return value, offset
    raise ValueError('Overlong binding LEB128')


def decode_stream(data, lazy=False, weak=False):
    offset = 0
    ordinal = -3 if weak else 0
    symbol = None
    records = []
    while offset < len(data):
        byte = data[offset]
        offset += 1
        opcode, immediate = byte & 0xf0, byte & 0xf
        if opcode in (0x20, 0x60, 0x80, 0x90, 0xa0, 0xc0) and immediate:
            raise ValueError('Nonzero reserved binding immediate')
        count = None
        if opcode == 0:
            if immediate:
                raise ValueError('Unknown binding DONE immediate')
            if lazy:
                ordinal, symbol = 0, None
                continue
            if any(data[offset:]):
                raise ValueError('Unexpected bytes after binding DONE')
            break
        elif opcode == 0x10:
            ordinal = immediate
        elif opcode == 0x20:
            ordinal, offset = leb(data, offset)
        elif opcode == 0x30:
            ordinal = immediate - 16 if immediate else 0
            if ordinal < -3:
                raise ValueError('Unknown special library ordinal')
        elif opcode == 0x40:
            if immediate & ~0x9:
                raise ValueError('Unknown binding symbol flags')
            end = data.find(b'\0', offset)
            if end < 0:
                raise ValueError('Unterminated binding symbol')
            symbol = data[offset:end].decode('utf-8')
            if not symbol:
                raise ValueError('Empty binding symbol')
            offset = end+1
        elif opcode == 0x50:
            if immediate not in (1, 2, 3):
                raise ValueError('Unknown binding type')
        elif opcode == 0x60:
            _, offset = leb(data, offset, signed=True)
        elif opcode in (0x70, 0x80):
            _, offset = leb(data, offset)
        elif opcode in (0x90, 0xb0):
            count = 1
        elif opcode == 0xa0:
            count = 1
            _, offset = leb(data, offset)
        elif opcode == 0xc0:
            count, offset = leb(data, offset)
            _, offset = leb(data, offset)
        else:
            raise ValueError('Unsupported binding opcode: '+hex(byte))
        if count:
            if symbol is None:
                raise ValueError('Binding with no symbol')
            records.append({'ordinal': ordinal, 'symbol': symbol, 'count': count})
    return records


def classic_bindings(raw):
    data = arm64(raw)
    cs = commands(data)
    if any(cmd == 0x80000034 for cmd, _, _ in cs):
        raise ValueError('Chained fixups are not supported by the optional-load guard')
    infos = [(offset, size) for cmd, offset, size in cs if cmd in (0x22, 0x80000022)]
    if len(infos) != 1 or infos[0][1] != 48:
        raise ValueError('Expected one classic dyld-info command')
    libs = [string(data, offset+unpack('<I', data, offset+8)[0], offset+size)
            for cmd, offset, size in cs if cmd in DYLIBS]
    records = []
    info, _ = infos[0]
    command_end = 32+unpack('<I', data, 20)[0]
    for kind, field in [('bind', 16), ('weak_bind', 24), ('lazy_bind', 32)]:
        start, size = unpack('<II', data, info+field)
        if not size:
            continue
        if start < command_end or start+size > len(data):
            raise ValueError('Binding stream outside payload')
        for record in decode_stream(data[start:start+size], lazy=kind == 'lazy_bind', weak=kind == 'weak_bind'):
            ordinal = record['ordinal']
            if ordinal > len(libs):
                raise ValueError('Binding library ordinal outside load list')
            records.append({**record, 'stream': kind, 'library': libs[ordinal-1] if ordinal > 0 else None})
    return records
