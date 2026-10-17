#!/usr/bin/env python3
"""Capture actual compiler ABI references for the first AppKit Swift-overlay failure."""
import json
import subprocess
from pathlib import Path
from loader_plan import load_json
from capture_loader_contracts import declarations


def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, timeout=180, **kwargs)


def main():
    root = Path(__file__).resolve().parents[1]
    out = root/'reports'
    out.mkdir(exist_ok=True)
    failure = json.loads((root/'docs/evidence/real-loader-latest.json').read_text())['first_failure']
    name = '/usr/lib/swift/libswiftAppKit.dylib'
    if failure != {'kind': 'library_not_loaded', 'name': name}:
        raise SystemExit('Refusing to capture a different first failure')
    symbols = load_json(root/'docs/evidence/dependencies-16.55.json.gz')['system_imports'][name]
    sdk = run('xcrun', '--sdk', 'macosx', '--show-sdk-path').strip()
    target = ['-sdk', sdk, '-target', 'arm64-apple-macos11.0']
    sil = run('xcrun', 'swiftc', *target, '-parse-as-library', '-module-name', 'ExcelOverlayProbe', '-emit-silgen', str(root/'tools/swift_appkit_probe.swift'))
    ir = run('xcrun', 'swiftc', *target, '-parse-as-library', '-module-name', 'ExcelOverlayProbe', '-emit-ir', str(root/'tools/swift_appkit_probe.swift'))
    force_lines = [line.strip() for line in ir.splitlines() if '_swift_FORCE_LOAD_$_swiftAppKit' in line]
    if not any('external global i1' in line for line in force_lines):
        raise RuntimeError('Unexpected compiler force-load declaration; refuse native data read')
    refs = []
    for symbol in symbols:
        mangled = symbol.removeprefix('_')
        refs.append({'symbol': symbol, 'demangled': run('xcrun', 'swift-demangle', '--compact', symbol).strip(),
            'compiler_reference_lines': [line.strip() for line in sil.splitlines() if mangled in line]})
    ast = run('xcrun', 'clang', '-target', 'arm64-apple-macos11.0', '-isysroot', sdk,
              '-x', 'objective-c', '-fsyntax-only', '-Xclang', '-ast-dump=json',
              '-Xclang', '-ast-dump-filter', '-Xclang', 'NSCompositingOperation', '-', input='#import <AppKit/AppKit.h>\n')
    enum = []
    for node in declarations(ast):
        if node.get('name') != 'NSCompositingOperation':
            continue
        record = {'kind': node.get('kind'), 'type': node.get('type'), 'underlying_type': node.get('fixedUnderlyingType'), 'constants': []}
        previous = -1
        for child in node.get('inner', []):
            if child.get('kind') != 'EnumConstantDecl':
                continue
            pending = list(child.get('inner', []))
            value = None
            while pending:
                expr = pending.pop()
                if expr.get('kind') == 'ConstantExpr' and 'value' in expr:
                    value = int(expr['value'])
                    break
                pending.extend(expr.get('inner', []))
            previous = previous+1 if value is None else value
            record['constants'].append({'name': child['name'], 'value': previous})
        enum.append(record)
    executable = root/'build/swift-appkit-values'
    executable.parent.mkdir(exist_ok=True)
    try:
        run('xcrun', 'swiftc', *target, str(root/'tools/swift_appkit_values.swift'), '-o', str(executable))
        run(str(executable), str(out/'swift-appkit-values.json'))
    finally:
        executable.unlink(missing_ok=True)
    report = {'scope': 'Actual Mac compiler lowering and valid two-component IndexPath behavior only. No iOS compatibility, rendering or Excel startup proven.',
        'failure': failure, 'sdk': sdk, 'compiler': run('xcrun', 'swiftc', '--version').strip(),
        'symbols': refs, 'force_load_compiler_ir': force_lines, 'operation_declarations': enum, 'overlay_implemented': False}
    (out/'swift-appkit-contracts.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Captured', len(refs), 'overlay imports; drawing and invalid-index behavior remain untested')


if __name__ == '__main__':
    main()
