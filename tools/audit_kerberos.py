#!/usr/bin/env python3
"""Audit real SDK declarations and Simulator GSS exports; never invoke auth APIs."""
import json
import os
import subprocess
from pathlib import Path

from capture_loader_contracts import declarations

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['GSS_C_NT_USER_NAME', 'krb5_free_context', 'krb5_free_host_realm',
         'krb5_get_host_realm', 'krb5_init_context']
GSS = '/System/Library/Frameworks/GSS.framework/GSS'


def command(*args, timeout=60):
    return subprocess.check_output(list(map(str, args)), text=True, timeout=timeout).strip()


def sdk_audit(kind, target):
    sdk = Path(command('xcrun', '--sdk', kind, '--show-sdk-path'))
    report = {'sdk': str(sdk), 'target': target, 'headers': [], 'stubs': []}
    for framework in ('Kerberos', 'GSS'):
        base = sdk/f'System/Library/Frameworks/{framework}.framework'
        header = base/f'Headers/{framework}.h'
        item = {'framework': framework, 'public_umbrella_present': header.is_file(),
                'declarations': [], 'unresolved': []}
        if header.is_file():
            for name in NAMES:
                argv = ['xcrun', 'clang', '-target', target, '-isysroot', str(sdk),
                        '-x', 'objective-c', '-fsyntax-only', '-Xclang', '-ast-dump=json',
                        '-Xclang', '-ast-dump-filter', '-Xclang', name, '-']
                compiled = subprocess.run(argv, input=f'#import <{framework}/{framework}.h>\n',
                                          text=True, capture_output=True, timeout=60)
                if compiled.returncode:
                    item['unresolved'].append({'name': name, 'compiler_error': compiled.stderr[-2000:]})
                    continue
                found = [node for node in declarations(compiled.stdout)
                         if node.get('name') == name and node.get('kind') in ('FunctionDecl', 'VarDecl')]
                for node in found:
                    item['declarations'].append({'name': name, 'kind': node['kind'], 'type': node.get('type'),
                        'parameters': [n.get('type') for n in node.get('inner', []) if n.get('kind') == 'ParmVarDecl']})
                if not found:
                    item['unresolved'].append({'name': name, 'reason': 'No exact declaration; a macro alias requires separate analysis'})
        report['headers'].append(item)
        stub = base/f'{framework}.tbd'
        report['stubs'].append({'path': str(stub), 'exists': stub.is_file(),
            'name_tokens_present': [name for name in NAMES if '_'+name in stub.read_text()] if stub.is_file() else [],
            'scope': 'Text occurrence only, not a parsed target export or runtime guarantee'})
    return report


def main():
    reports = ROOT/'reports'
    reports.mkdir(exist_ok=True)
    report = {'source_sha': os.environ.get('GITHUB_SHA'), 'names': NAMES,
              'scope': 'SDK declarations and export lookup only. No credentials, authentication calls, Office code or load substitutions.',
              'sdk_audits': []}
    path = reports/'kerberos-audit.json'
    udid = None
    try:
        for kind, target in [('macosx', 'arm64-apple-macos11.0'),
                             ('iphoneos', 'arm64-apple-ios18.0'),
                             ('iphonesimulator', 'arm64-apple-ios18.0-simulator')]:
            report['sdk_audits'].append(sdk_audit(kind, target))
            path.write_text(json.dumps(report, indent=2)+'\n')
        sdk = report['sdk_audits'][-1]['sdk']
        # Probe only the SDK-backed public GSS framework. Do not search or load
        # private authentication providers or borrow a macOS framework.
        if not Path(sdk+GSS+'.tbd').is_file():
            raise RuntimeError('Simulator public GSS stub absent; do not probe an unsupported provider')
        probe = reports/'gss-export-probe'
        command('xcrun', 'clang', '-target', 'arm64-apple-ios18.0-simulator', '-isysroot', sdk,
                '-Wall', '-Wextra', '-Werror', ROOT/'tests/loader/probe_system_library.c', '-o', probe)
        command('codesign', '--force', '--sign', '-', probe)
        devices = json.loads(command('xcrun', 'simctl', 'list', 'devices', 'available', '--json'))['devices']
        candidates = [(runtime, device) for runtime, items in devices.items() if 'iOS-' in runtime
                      for device in items if 'iPad' in device['name'] and device.get('isAvailable')]
        candidates.sort(key=lambda x: ('M4' not in x[1]['name'], 'Pro' not in x[1]['name'], x[0]))
        if not candidates:
            raise RuntimeError('No available iPad Simulator')
        runtime, device = candidates[0]
        report['device'] = device['name']
        report['runtime'] = runtime
        udid = command('xcrun', 'simctl', 'create', 'KerberosAudit-'+os.environ.get('GITHUB_RUN_ID', 'local'),
                       device['deviceTypeIdentifier'], runtime)
        command('xcrun', 'simctl', 'boot', udid)
        command('xcrun', 'simctl', 'bootstatus', udid, '-b', timeout=240)
        manifest = reports/'gss-probe.tsv'
        manifest.write_text('LIB\t'+GSS+'\n'+''.join('SYM\t'+n+'\n' for n in NAMES))
        checked = subprocess.run(['xcrun', 'simctl', 'spawn', udid, str(probe), '--manifest', str(manifest)],
                                 text=True, capture_output=True, timeout=300)
        (reports/'gss-probe.stdout.log').write_text(checked.stdout)
        (reports/'gss-probe.stderr.log').write_text(checked.stderr)
        checked.check_returncode()
        report['runtime_lookup'] = checked.stdout.splitlines()
        rows = [line.split('\t') for line in checked.stdout.splitlines()]
        images = [r for r in rows if r[0] == 'IMAGE']
        if not images or any(len(r) != 3 or r[2] != '7' or '.simruntime/' not in r[1] for r in images):
            raise RuntimeError('GSS provider lacks confirmed Simulator platform 7 provenance')
        queried = [r[1] for r in rows if r[0] in ('FOUND', 'MISSING')]
        if sorted(queried) != sorted(NAMES):
            raise RuntimeError('Incomplete or duplicate symbol results')
        report['status'] = 'Audit captured; no replacement approved or implemented'
    except BaseException as error:
        report['error'] = str(error)
        raise
    finally:
        path.write_text(json.dumps(report, indent=2)+'\n')
        # This artifact must contain metadata only, never even our diagnostic executable.
        (reports/'gss-export-probe').unlink(missing_ok=True)
        if udid:
            for action in ('shutdown', 'delete'):
                subprocess.run(['xcrun', 'simctl', action, udid], capture_output=True, timeout=60)


if __name__ == '__main__':
    main()
