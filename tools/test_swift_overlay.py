#!/usr/bin/env python3
"""Check compiler-generated Swift exports before any Microsoft load redirection."""
import json
import subprocess
from pathlib import Path


def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, timeout=180, **kwargs)


def build_overlay(root, build, platform, required_version="0.0.0"):
    build.mkdir(parents=True, exist_ok=True)
    source = root/'experiments/swift-appkit'
    sdk_name, triple = {'macos':('macosx','arm64-apple-macos11.0'), 'simulator':('iphonesimulator','arm64-apple-ios18.0-simulator'), 'ios':('iphoneos','arm64-apple-ios18.0')}[platform]
    sdk = run('xcrun', '--sdk', sdk_name, '--show-sdk-path').strip()
    target = ['-sdk', sdk, '-target', triple]
    objects = []
    for index, path in enumerate([source/'OverlayRuntime.m', root/'shim/ExcelShim.m']):
        obj = build/f'runtime-{index}.o'
        run('xcrun', 'clang', '-target', triple, '-isysroot', sdk,
            '-fobjc-arc', '-Wall', '-Wextra', '-Werror', '-I'+str(root/'shim'),
            '-I'+str(source), '-c', str(path), '-o', str(obj))
        objects.append(str(obj))
    marker = build/'force-load.o'
    run('xcrun', 'swiftc', *target, '-parse-as-library', '-module-name', 'ExcelOverlayForce',
        '-module-link-name', 'swiftAppKit', '-Xfrontend', '-autolink-force-load',
        '-emit-object', str(source/'ForceLoad.swift'), '-o', str(marker))
    objects.append(str(marker))
    library = build/'libExcelSwiftAppKit.dylib'
    run('xcrun', 'swiftc', *target, '-module-name', 'AppKit', '-module-link-name', 'ExcelSwiftAppKit', '-I', str(source),
        '-emit-library', '-emit-module', '-emit-module-path', str(build/'AppKit.swiftmodule'),
        str(source/'AppKit.swift'), *objects, '-o', str(library),
        '-Xlinker', '-install_name', '-Xlinker', '@rpath/libExcelSwiftAppKit.dylib',
        '-Xlinker', '-compatibility_version', '-Xlinker', required_version,
        '-Xlinker', '-current_version', '-Xlinker', required_version)
    export_types = {line.split()[-1]:line.split()[-2] for line in run('nm', '-gU', str(library)).splitlines() if len(line.split()) >= 2}
    exports = set(export_types)
    baseline = json.loads((root/'reports/swift-appkit-contracts.json').read_text())
    required = [entry['symbol'] for entry in baseline['symbols']]
    if set(required)-exports:
        raise RuntimeError('Missing exact Swift exports: '+repr(sorted(set(required)-exports)))
    if any(export_types[name].upper() != 'T' for name in required if name.startswith('_$s')):
        raise RuntimeError('Both callable Swift overlay exports must be functions')
    if export_types['__swift_FORCE_LOAD_$_swiftAppKit'].upper() not in ('S','D','B','C'):
        raise RuntimeError('Expected compiler-generated marker data export')
    return library, required


def main():
    root = Path(__file__).resolve().parents[1]
    build = root/'build/swift-overlay-prototype'
    build.mkdir(parents=True, exist_ok=True)
    reports = root/'reports'
    reports.mkdir(exist_ok=True)
    source = root/'experiments/swift-appkit'
    sdk = run('xcrun', '--sdk', 'macosx', '--show-sdk-path').strip()
    target = ['-sdk', sdk, '-target', 'arm64-apple-macos11.0']
    library, required = build_overlay(root, build, 'macos')
    executable = build/'client'
    run('xcrun', 'swiftc', *target, '-I', str(build), '-I', str(source), '-L', str(build),
        '-lExcelSwiftAppKit', '-Xlinker', '-rpath', '-Xlinker', str(build),
        str(root/'tools/swift_overlay_client.swift'), '-o', str(executable))
    run(str(executable), str(reports/'swift-overlay-prototype.json'))
    original = json.loads((reports/'swift-appkit-values.json').read_text())
    actual = json.loads((reports/'swift-overlay-prototype.json').read_text())
    for key in ('index_path_samples', 'index_path_layout', 'rect_layout', 'operation_layout'):
        if original[key] != actual[key]:
            raise RuntimeError('Native comparison failed: '+key)
    (reports/'swift-overlay-validation.json').write_text(json.dumps({
        'exact_required_exports_checked':required, 'native_index_path_cases_checked':5,
        'native_layouts_match':True, 'force_marker_emitted_by_swift_compiler':True,
        'drawing_implemented':False, 'ios_cross_abi_checked':False,
        'microsoft_executed':False}, indent=2)+'\n')
    print('Exact exports and five native getter cases matched; no iOS or drawing compatibility inferred')


if __name__ == '__main__':
    main()
