#!/usr/bin/env python3
"""Build distinct forwarding dylibs; never fabricate missing exports or API behavior."""
import argparse
import json
import subprocess
from pathlib import Path
from macho import inspect, arm64, commands, unpack
from excel_retarget import ver


def build_one(shim, output, install_name, required_version, platform):
    if output.exists() or output.resolve() == shim.resolve():
        raise ValueError('Facade output must be new and distinct from the input shim')
    sdk_name = 'iphoneos' if platform == 'ios' else 'macosx'
    sdk = subprocess.check_output(['xcrun', '--sdk', sdk_name, '--show-sdk-path'], text=True).strip()
    clang = subprocess.check_output(['xcrun', '--find', 'clang'], text=True).strip()
    target = 'arm64-apple-ios18.0' if platform == 'ios' else 'arm64-apple-macos11.0'
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([clang, '-target', target, '-isysroot', sdk, '-Wall', '-Wextra', '-Werror',
                    '-dynamiclib', '-x', 'c', '-', '-install_name', install_name,
                    '-compatibility_version', required_version, '-current_version', required_version,
                    '-Xlinker', '-reexport_library', '-Xlinker', str(shim.resolve()),
                    '-Xlinker', '-rpath', '-Xlinker', '@loader_path', '-o', str(output)],
                   input='/* This facade only reexports the existing shim. */\n', text=True, check=True)
    subprocess.run(['codesign', '--force', '--sign', '-', str(output)], check=True)
    subprocess.run(['codesign', '--verify', '--strict', str(output)], check=True)
    metadata = inspect(output.read_bytes())
    shim_metadata = inspect(shim.read_bytes())
    expected_platform = 2 if platform == 'ios' else 1
    if metadata.get('install_name') != install_name or metadata['build_versions'][0]['platform'] != expected_platform:
        raise ValueError('Unexpected facade identity or platform')
    reexports = [d['path'] for d in metadata['dylibs'] if d['kind'] == 'reexport']
    if reexports != [shim_metadata['install_name']]:
        raise ValueError('Facade does not reexport exactly the supplied shim')
    data = arm64(output.read_bytes())
    ids = [o for c, o, _ in commands(data) if c == 0xd]
    if len(ids) != 1 or unpack('<II', data, ids[0]+16) != (ver(required_version), ver(required_version)):
        raise ValueError('Unexpected facade version')
    return {'install_name': install_name, 'required_compatibility_version': required_version,
            'reexports': reexports, 'platform': expected_platform, 'signed_and_verified': True,
            'does_not_implement_missing_APIs': True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan', type=Path, required=True)
    ap.add_argument('--shim', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    plan = json.loads(args.plan.read_text())
    entries = []
    for facade in plan['facades']:
        name = facade['install_name']
        if not name.startswith('@rpath/') or Path(name).name != name[7:]:
            raise ValueError('Expected a flat @rpath facade name')
        entries.append(build_one(args.shim, args.output/name[7:], name,
                                 facade['required_compatibility_version'], 'ios'))
    args.report.write_text(json.dumps({'facades': entries, 'excel_executed': False,
                                      'loader_ready': False, 'release_ready': False}, indent=2)+'\n')
    print('Built and signed iOS forwarding libraries. No missing API stubs or IPA produced.')


if __name__ == '__main__':
    main()
