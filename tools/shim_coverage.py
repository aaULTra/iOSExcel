#!/usr/bin/env python3
"""Report exact AppKit import/export names; symbol presence is NOT API correctness."""
import argparse
import gzip
import json
from pathlib import Path


def report(dependencies, nm_text):
    required = set(dependencies['closure_appkit_symbols'])
    exported = {line.split()[-1] for line in nm_text.splitlines() if line.split()}
    present = sorted(required & exported)
    missing = sorted(required - exported)
    classes = {name for name in required if name.startswith('_OBJC_CLASS_$_')}
    return {
        'scope': 'Excel 16.55 resolved arm64 startup closure, AppKit imports only',
        'meaning': 'Exact exported names only. Does not validate ABI, behavior, initialization or device execution.',
        'required_count': len(required),
        'exported_name_count': len(present),
        'missing_count': len(missing),
        'required_class_count': len(classes),
        'exported_class_count': len(classes & exported),
        'exported_names': present,
        'missing_names': missing,
        'loader_ready': False,
        'release_ready': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dependencies', type=Path)
    parser.add_argument('nm_exports', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raw = args.dependencies.read_bytes()
    graph = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
    result = report(graph, args.nm_exports.read_text())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"AppKit names exported: {result['exported_name_count']}/{result['required_count']}; "
          f"classes: {result['exported_class_count']}/{result['required_class_count']}. "
          'Name coverage is not runtime compatibility. No release readiness claimed.')


if __name__ == '__main__':
    main()
