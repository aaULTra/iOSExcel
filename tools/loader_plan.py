#!/usr/bin/env python3
"""Hash-verified AppKit/Cocoa redirection experiment on the selected startup closure.

Outputs modified binaries only, never a runnable app or IPA. Does not claim remaining
imports, resource lookup, activation or behavior are compatible with iPadOS.
"""
import argparse
import gzip
import hashlib
import json
import tempfile
from pathlib import Path, PurePosixPath
from excel_retarget import retarget
from macho import arm64, commands, DYLIBS, unpack, string, version

REDIRECTS = {
    '/System/Library/Frameworks/AppKit.framework/Versions/C/AppKit': '@rpath/ExcelAppKit.dylib',
    '/System/Library/Frameworks/Cocoa.framework/Versions/A/Cocoa': '@rpath/ExcelCocoa.dylib',
    '/System/Library/Frameworks/ApplicationServices.framework/Versions/A/ApplicationServices': '@rpath/ExcelApplicationServices.dylib',
    '/System/Library/Frameworks/Kerberos.framework/Versions/A/Kerberos': '@rpath/ExcelKerberos.dylib',
    '/System/Library/Frameworks/ServiceManagement.framework/Versions/A/ServiceManagement': '@rpath/ExcelServiceManagement.dylib',
    '/System/Library/Frameworks/SecurityInterface.framework/Versions/A/SecurityInterface': '@rpath/ExcelSecurityInterface.dylib',
    '/System/Library/Frameworks/ScriptingBridge.framework/Versions/A/ScriptingBridge': '@rpath/ExcelScriptingBridge.dylib',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_json(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)


def source_path(root, name):
    rel = PurePosixPath(name)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:
        raise ValueError('Unsafe closure path: ' + name)
    path = root.joinpath(*rel.parts)
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink() or not path.is_file():
        raise ValueError('Missing, external or symlinked binary: ' + name)
    return path


def payload_hashes(data):
    hashes = {}
    for command, offset, _ in commands(data):
        if command != 0x19:
            continue
        segment = data[offset+8:offset+24].split(b'\0', 1)[0].decode('ascii')
        if segment == '__LINKEDIT':
            fileoff, size = unpack('<QQ', data, offset + 40)
            if fileoff + size > len(data):
                raise ValueError('Link-edit segment exceeds file')
            hashes['__LINKEDIT'] = sha(data[fileoff:fileoff+size])
        for i in range(unpack('<I', data, offset + 64)[0]):
            q = offset + 72 + i * 80
            name = data[q:q+16].split(b'\0', 1)[0].decode('ascii')
            if name == '__text':
                _, size, fileoff = unpack('<QQI', data, q+32)
                if fileoff + size > len(data):
                    raise ValueError('Text section exceeds file')
                hashes[segment + ',' + name] = sha(data[fileoff:fileoff+size])
    if '__LINKEDIT' not in hashes:
        raise ValueError('Expected link-edit payload')
    return hashes


def plan(root, inventory, graph, minos='18.0', sdk='18.0', platform=2):
    nodes = {b['path']: b for b in inventory['binaries']}
    closure = graph['startup_closure']
    if len(closure) != len(set(closure)) or graph['main'] not in closure:
        raise ValueError('Invalid startup closure')
    images = []
    requirements = {old: 0 for old in REDIRECTS}
    both = []
    for name in sorted(closure):
        path = source_path(root, name)
        raw = path.read_bytes()
        if name not in nodes or sha(raw) != nodes[name]['sha256']:
            raise ValueError('Binary differs from recorded inventory: ' + name)
        before = arm64(raw)
        expected_type = 2 if name == graph['main'] else 6
        if unpack('<I', before, 12)[0] != expected_type:
            raise ValueError('Unexpected closure filetype: ' + name)
        paths = []
        for command, offset, size in commands(before):
            if command not in DYLIBS:
                continue
            lib = string(before, offset + unpack('<I', before, offset+8)[0], offset+size)
            paths.append(lib)
            if lib in requirements:
                requirements[lib] = max(requirements[lib], unpack('<I', before, offset+20)[0])
        if paths != [edge['path'] for edge in graph['graph'][name]]:
            raise ValueError('Dependency graph differs from binary: ' + name)
        if all(old in paths for old in ('/System/Library/Frameworks/AppKit.framework/Versions/C/AppKit', '/System/Library/Frameworks/Cocoa.framework/Versions/A/Cocoa')):
            both.append(name)
        after, events = retarget(raw, minos, sdk, REDIRECTS, platform=platform)
        before_hashes, after_hashes = payload_hashes(before), payload_hashes(after)
        if before_hashes != after_hashes:
            raise ValueError('Executable or link-edit payload changed: ' + name)
        images.append({'path': name, 'input_sha256': sha(raw), 'arm64_before_sha256': sha(before),
                       'arm64_after_sha256': sha(after), 'payload_hashes_unchanged': before_hashes,
                       'modifications': events})
    return {'status': 'Binary-only redirection experiment; signatures stale; not a runnable Excel bundle',
            'image_count': len(images), 'images_loading_both_facades': both,
            'redirects': REDIRECTS,
            'facades': [{'original': old, 'install_name': REDIRECTS[old],
                         'required_compatibility_version': version(value),
                         'version_scope': 'Loader numeric requirement only; no API compatibility claim'}
                        for old, value in requirements.items()],
            'minos': minos, 'sdk': sdk, 'platform': platform, 'images': images,
            'unresolved': [edge for edge in graph['unresolved'] if edge['from'] in closure], 'remaining_system_libraries': sorted({edge['path']
                for name in closure for edge in graph['graph'][name]
                if edge['category'] == 'system' and edge['path'] not in REDIRECTS}),
            'excel_executed': False, 'loader_ready': False, 'release_ready': False}


def stage(root, destination, result):
    root, destination = root.resolve(), destination.resolve()
    if destination.exists() or destination.is_relative_to(root) or root.is_relative_to(destination):
        raise ValueError('Destination must be new and non-overlapping')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix='.excel-closure-') as tmp:
        output = Path(tmp) / 'images'
        output.mkdir()
        for image in result['images']:
            source = source_path(root, image['path'])
            raw = source.read_bytes()
            if sha(raw) != image['input_sha256']:
                raise ValueError('Source changed after validation')
            changed, _ = retarget(raw, result['minos'], result['sdk'], result['redirects'], platform=result.get('platform', 2))
            if sha(changed) != image['arm64_after_sha256']:
                raise ValueError('Non-deterministic retarget result')
            target = output / image['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(changed)
            target.chmod(source.stat().st_mode & 0o777)
        output.rename(destination)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('app', type=Path)
    ap.add_argument('--inventory', type=Path, required=True)
    ap.add_argument('--graph', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--output-binaries', type=Path)
    args = ap.parse_args()
    result = plan(args.app, load_json(args.inventory), load_json(args.graph))
    if args.output_binaries:
        stage(args.app, args.output_binaries, result)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(f"Validated {result['image_count']} images; {len(result['images_loading_both_facades'])} load both AppKit and Cocoa. No Excel execution or IPA.")


if __name__ == '__main__':
    main()
