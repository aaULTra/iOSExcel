#!/usr/bin/env python3
"""Native two-level binding contract using only our own small C fixture."""
import json
import shutil
import subprocess
from pathlib import Path
from build_facades import build_one
from excel_retarget import rewrite_load_paths
from macho import inspect
from loader_plan import payload_hashes


def main():
    root = Path(__file__).resolve().parents[1]
    out = root / 'build/loader-contract'
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    sdk = subprocess.check_output(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip()
    compiler = ['xcrun', 'clang', '-target', 'arm64-apple-macos11.0', '-isysroot', sdk,
                '-Wall', '-Wextra', '-Werror']
    originals = out / 'original-desktop-frameworks'
    originals.mkdir()
    mapping = {}
    for name, source, version in [('AppKit', 'appkit.c', '45.0'), ('Cocoa', 'cocoa.c', '1.0')]:
        install = '@rpath/original-desktop-frameworks/Original'+name+'.dylib'
        library = originals / ('Original'+name+'.dylib')
        subprocess.run(compiler + ['-dynamiclib', str(root/'tests/loader'/source),
                                  '-install_name', install, '-compatibility_version', version,
                                  '-current_version', version, '-o', str(library)], check=True)
        mapping[install] = '@rpath/Excel'+name+'.dylib'
    client = out / 'client'
    subprocess.run(compiler + [str(root/'tests/loader/client.c'),
                              str(originals/'OriginalAppKit.dylib'), str(originals/'OriginalCocoa.dylib'),
                              '-Xlinker', '-rpath', '-Xlinker', '@executable_path', '-o', str(client)], check=True)
    subprocess.run([str(client)], check=True)
    original = client.read_bytes()
    before = inspect(original)
    changed, events = rewrite_load_paths(original, mapping)
    after = inspect(changed)
    names = ['_EXLoaderAppKitValue', '_EXLoaderCocoaValue']
    bindings = []
    for name in names:
        old = next(x for x in before['undefined'] if x['name'] == name)
        new = next(x for x in after['undefined'] if x['name'] == name)
        if old['ordinal'] != new['ordinal'] or new['library'] != mapping[old['library']]:
            raise ValueError('Two-level import binding did not retain its ordinal')
        bindings.append({'symbol': name, 'ordinal': old['ordinal'], 'before': old['library'], 'after': new['library']})
    if len({b['ordinal'] for b in bindings}) != 2:
        raise ValueError('Fixture must import from two different library ordinals')
    if payload_hashes(original) != payload_hashes(changed):
        raise ValueError('Link-edit or text bytes changed')
    client.write_bytes(changed)
    subprocess.run(['codesign', '--force', '--sign', '-', str(client)], check=True)
    subprocess.run(['codesign', '--verify', '--strict', str(client)], check=True)
    shim = out/'libFixtureShim.dylib'
    subprocess.run(compiler + ['-dynamiclib', str(root/'tests/loader/shared.c'),
                              '-install_name', '@rpath/libFixtureShim.dylib', '-o', str(shim)], check=True)
    facades = []
    for name, version in [('AppKit', '45.0'), ('Cocoa', '1.0')]:
        facades.append(build_one(shim, out/('Excel'+name+'.dylib'), '@rpath/Excel'+name+'.dylib', version, 'macos'))
    shutil.rmtree(originals)
    # With originals absent this succeeds only if the rewritten two-level bindings work.
    subprocess.run([str(client)], check=True)
    report = {'native_fixture_passed': True, 'original_libraries_removed_before_final_run': True,
              'binding_ordinals_preserved': bindings, 'text_and_linkedit_unchanged_before_signing': True,
              'modifications': events, 'facades': facades, 'excel_executed': False}
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
