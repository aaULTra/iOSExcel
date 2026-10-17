#!/usr/bin/env python3
"""Read actual macOS SDK declarations for the first missing Apple framework.
No Office code executes. Reports interface facts only, not SDK source/AST bodies.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path
from loader_plan import load_json


def declarations(text):
    decoder = json.JSONDecoder()
    cursor = 0
    while cursor < len(text):
        if text[cursor].isspace():
            cursor += 1
            continue
        node, cursor = decoder.raw_decode(text, cursor)
        yield node


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--result', type=Path, required=True)
    ap.add_argument('--graph', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    failure = json.loads(args.result.read_text()).get('first_failure', {})
    name = failure.get('name', '')
    match = re.fullmatch(r'/System/Library/Frameworks/([A-Za-z0-9_]+)\.framework/(?:Versions/[^/]+/)?\1', name)
    result = {'scope': 'Actual Mac SDK interface declarations; no runtime behavior guarantee',
              'first_failure': failure, 'declarations': [], 'unresolved': []}
    if not match or failure.get('kind') != 'library_not_loaded':
        result['status'] = 'First failure is not a simple public Apple framework path'
    else:
        framework = match[1]
        sdk = subprocess.check_output(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip()
        result['sdk'] = sdk
        header = Path(sdk)/f'System/Library/Frameworks/{framework}.framework/Headers/{framework}.h'
        if not header.is_file():
            result['status'] = 'No public umbrella header in actual SDK'
        else:
            graph = load_json(args.graph)
            required = graph['system_imports'].get(name, [])
            result['required_names'] = required
            source = f'#import <{framework}/{framework}.h>\n'
            for symbol in required:
                identifier = symbol.removeprefix('_')
                if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', identifier):
                    result['unresolved'].append({'name': symbol, 'reason': 'Not a C identifier'})
                    continue
                command = ['xcrun', 'clang', '-target', 'arm64-apple-macos11.0', '-isysroot', sdk,
                           '-x', 'objective-c', '-fsyntax-only', '-Xclang', '-ast-dump=json',
                           '-Xclang', '-ast-dump-filter', '-Xclang', identifier, '-']
                compiled = subprocess.run(command, input=source, text=True, capture_output=True, timeout=60)
                if compiled.returncode:
                    result['unresolved'].append({'name': symbol, 'reason': compiled.stderr[-2000:]})
                    continue
                found = False
                for node in declarations(compiled.stdout):
                    if node.get('name') != identifier or node.get('kind') not in ('FunctionDecl', 'VarDecl', 'EnumConstantDecl'):
                        continue
                    result['declarations'].append({'name': identifier, 'kind': node['kind'],
                        'type': node.get('type'), 'location': node.get('loc'),
                        'parameters': [{'name': p.get('name'), 'type': p.get('type')}
                                       for p in node.get('inner', []) if p.get('kind') == 'ParmVarDecl']})
                    found = True
                if not found:
                    result['unresolved'].append({'name': symbol, 'reason': 'No matching declaration from the public umbrella header'})
            result['status'] = 'Interface capture complete; unresolved declarations remain explicit'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(result['status'], len(result['declarations']), 'declarations;', len(result['unresolved']), 'unresolved')


if __name__ == '__main__':
    main()
