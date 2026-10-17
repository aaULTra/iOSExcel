#!/usr/bin/env python3
"""Capture actual compiler ABI references for the first AppKit Swift-overlay failure."""
import json
import re
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
    sil = run('xcrun', 'swiftc', *target, '-parse-as-library', '-module-name', 'ExcelOverlayProbe', '-emit-silgen', '-o', '-', str(root/'tools/swift_appkit_probe.swift'))
    ir = run('xcrun', 'swiftc', *target, '-parse-as-library', '-module-name', 'ExcelOverlayProbe', '-emit-ir', '-o', '-', str(root/'tools/swift_appkit_probe.swift'))
    force_lines = [line.strip() for line in ir.splitlines() if '_swift_FORCE_LOAD_$_swiftAppKit' in line]
    (out/'swift-force-load-ir.json').write_text(json.dumps({'references': force_lines, 'scope': 'Own compiler probe LLVM references, no Apple implementation'}, indent=2)+'\n')
    anchor_ir = run('xcrun', 'swiftc', *target, '-parse-as-library', '-module-name', 'ExcelOverlayForce',
                    '-module-link-name', 'swiftAppKit', '-Xfrontend', '-autolink-force-load', '-emit-ir', '-o', '-',
                    str(root/'experiments/swift-appkit/ForceLoad.swift'))
    anchor = re.search(r'define[^\n]*void @"?_swift_FORCE_LOAD_\$_swiftAppKit"?\(\)[^{]*\{(.*?)^}', anchor_ir, re.S | re.M)
    (out/'swift-explicit-marker-ir.json').write_text(json.dumps({'lines': [line for line in anchor_ir.splitlines() if 'FORCE_LOAD' in line], 'source':'own empty Swift module compiler output'},indent=2)+'\n')
    if not anchor or 'ret void' not in anchor[0]:
        print('EXPLICIT_MARKER_LINES',json.dumps([line for line in anchor_ir.splitlines() if 'FORCE_LOAD' in line]),flush=True)
        raise RuntimeError('Compiler did not emit the expected void force-load function')
    inventory = load_json(root/'docs/evidence/excel-16.55.json.gz')
    closure = load_json(root/'docs/evidence/dependencies-16.55.json.gz')['startup_closure']
    marker_uses = [{'path': binary['path'], 'weak': entry['weak']} for binary in inventory['binaries']
                   if binary['path'] in closure for entry in binary.get('undefined', [])
                   if entry['name'] == '__swift_FORCE_LOAD_$_swiftAppKit']
    if len(marker_uses) != 4 or not all(row['weak'] for row in marker_uses):
        raise RuntimeError('Unexpected Office force-load import contract')
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
        'symbols': refs, 'force_load_compiler_ir': force_lines, 'explicit_compiler_anchor_ir': anchor[0].splitlines(), 'office_marker_imports': marker_uses, 'operation_declarations': enum, 'overlay_implemented': False}
    (out/'swift-appkit-contracts.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Captured', len(refs), 'overlay imports; drawing and invalid-index behavior remain untested')


if __name__ == '__main__':
    main()
