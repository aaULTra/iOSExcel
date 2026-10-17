#!/usr/bin/env python3
"""Internal real-Excel dyld experiment. No vendor payload or IPA is published.

Simulator platform 7 is deliberately separate from device platform 2. This runs
the original MH_EXECUTE through simctl spawn, not dlopen(MH_EXECUTE), and does
not claim installed-app lifecycle, activation, or device compatibility.
"""
import argparse
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

from build_facades import build_one
from excel_retarget import rewrite_load_paths, weaken_unused_loads
from loader_plan import load_json, plan, stage


def output(*args, timeout=120):
    return subprocess.check_output(list(map(str, args)), text=True, timeout=timeout).strip()


def run(*args):
    subprocess.run(list(map(str, args)), check=True)


def sdk_stub(sdk, install):
    path = sdk/install.lstrip('/')
    return path.with_suffix('.tbd') if path.suffix == '.dylib' else Path(str(path)+'.tbd')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('app', type=Path)
    ap.add_argument('--system-path-map', type=Path)
    ap.add_argument('--optional-frameworks', type=Path)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    reports = root/'reports'
    reports.mkdir(exist_ok=True)
    destination = root/'private/real-loader'
    graph = load_json(root/'docs/evidence/dependencies-16.55.json.gz')
    result = plan(args.app, load_json(root/'docs/evidence/excel-16.55.json.gz'), graph, platform=7)
    stage(args.app, destination, result)
    path_entries = json.loads(args.system_path_map.read_text()) if args.system_path_map else []
    sdk = Path(output('xcrun', '--sdk', 'iphonesimulator', '--show-sdk-path'))
    known = {entry['original'] for entry in path_entries}
    result['sdk_counterparts_absent'] = []
    # The same Versions-path failure was observed for Security and Accelerate.
    # Normalize this class of path only where both SDK and runtime checks pass.
    original_system_names = {edge['path'] for node in graph['startup_closure']
                             for edge in graph['graph'][node] if edge['category'] == 'system'}
    for old in sorted(original_system_names):
        new = re.sub(r'/Versions/[^/]+', '', old)
        if old in known or old == new or not old.startswith('/System/Library/Frameworks/'):
            continue
        stub = sdk_stub(sdk, new)
        if not stub.is_file():
            result['sdk_counterparts_absent'].append({'original': old, 'candidate': new})
            # Preflight only: do not run unsupported or host-macOS framework
            # initializers in the probe. Never automatically substitute these.
            path_entries.append({'original': old, 'target': new, 'map_eligible': False,
                                 'scope': 'SDK-absent counterpart presence audit only; no path substitution'})
            continue
        path_entries.append({'original': old, 'target': new, 'observed_failure_run': 38985243018,
                             'scope': 'Same verified versioned-path normalization; runtime load must pass'})
    if len({entry['target'] for entry in path_entries}) != len(path_entries):
        raise ValueError('Duplicate canonical counterpart needs an explicit alias analysis')
    for entry in path_entries:
        old, new = entry['original'], entry['target']
        if not old.startswith('/System/Library/Frameworks/') or not new.startswith('/System/Library/Frameworks/') or '..' in Path(new).parts:
            raise ValueError('Unexpected system library path mapping')
        if entry.get('map_eligible', True) and (not entry.get('observed_failure_run') or not sdk_stub(sdk, new).is_file()):
            raise ValueError('Counterpart needs failure evidence and an SDK declaration')
    result['system_path_modifications'] = []
    (reports/'real-loader-transform.json').write_text(json.dumps(result, indent=2)+'\n')
    frameworks = destination/'Contents/Frameworks'
    probe = destination/'probe-system-library'
    run('xcrun', 'clang', '-target', 'arm64-apple-ios18.0-simulator', '-isysroot', sdk,
        '-Wall', '-Wextra', '-Werror', root/'tests/loader/probe_system_library.c', '-o', probe)
    run('codesign', '--force', '--sign', '-', probe)
    shim = frameworks/'libExcelShim.dylib'
    sources = ['ExcelNibArchive.m', 'ExcelAppKit.m', 'ExcelShim.m', 'ExcelScreen.m', 'ExcelView.m', 'ExcelApplicationServices.m', 'ExcelKerberos.m']
    run('xcrun', 'clang', '-target', 'arm64-apple-ios18.0-simulator', '-isysroot', sdk,
        '-fobjc-arc', '-fmodules', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
        '-I'+str(root/'shim'), '-dynamiclib', *[root/'shim'/s for s in sources],
        '-framework', 'UIKit', '-framework', 'Foundation', '-framework', 'CoreGraphics', '-framework', 'GSS',
        '-install_name', '@rpath/libExcelShim.dylib', '-o', shim)
    run('codesign', '--force', '--sign', '-', shim)
    for facade in result['facades']:
        build_one(shim, frameworks/Path(facade['install_name']).name,
                  facade['install_name'], facade['required_compatibility_version'], 'simulator')
    devices = json.loads(output('xcrun', 'simctl', 'list', 'devices', 'available', '--json'))['devices']
    candidates = []
    for runtime, items in devices.items():
        if 'iOS-' not in runtime:
            continue
        version = tuple(int(v) for v in runtime.rsplit('iOS-', 1)[1].split('-'))
        if version[0] < 18:
            continue
        for device in items:
            if 'iPad' in device['name'] and device.get('isAvailable'):
                candidates.append((runtime, device, version))
    if not candidates:
        raise RuntimeError('No iPad simulator runtime installed')
    candidates.sort(key=lambda x: ('M4' not in x[1]['name'], 'Pro' not in x[1]['name'], tuple(-v for v in x[2])))
    runtime, template, _ = candidates[0]
    device_type = template.get('deviceTypeIdentifier')
    if not device_type:
        types = json.loads(output('xcrun', 'simctl', 'list', 'devicetypes', '--json'))['devicetypes']
        device_type = next(t['identifier'] for t in types if t['name'] == template['name'])
    udid = output('xcrun', 'simctl', 'create', 'RealExcelLoader-'+os.environ.get('GITHUB_RUN_ID', 'local'), device_type, runtime)
    report = {'experiment': 'Original Excel MH_EXECUTE with original 54-image Microsoft closure',
              'platform': 'iOS Simulator (7), not an iPadOS device build',
              'device': template['name'], 'runtime': runtime, 'source_sha': os.environ.get('GITHUB_SHA'),
              'microsoft_entrypoint_confirmed': False, 'excel_initialised': False,
              'activation_verified': False, 'release_ready': False}
    print('Launching real Excel loader on', template['name'], runtime, flush=True)
    try:
        run('xcrun', 'simctl', 'boot', udid)
        subprocess.run(['xcrun', 'simctl', 'bootstatus', udid, '-b'], check=True, timeout=240)
        manifest = destination/'system-probes.tsv'
        lines = []
        for entry in path_entries:
            lines.append(('LIB\t' if entry.get('map_eligible', True) else 'PREFLIGHT\t')+entry['target'])
            names = [name.removeprefix('_') for name in graph['system_imports'].get(entry['original'], [])]
            if any(any(c in value for c in '\t\r\n') for value in [entry['target'], *names]):
                raise ValueError('Unexpected control characters in probe inputs')
            lines.extend('SYM\t'+name for name in names)
        manifest.write_text('\n'.join(lines)+'\n')
        try:
            checked = subprocess.run(['xcrun', 'simctl', 'spawn', udid, str(probe), '--manifest', str(manifest)],
                                     text=True, capture_output=True, timeout=300)
        except subprocess.TimeoutExpired as error:
            def decode(value):
                return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
            report['status'] = 'Infrastructure/probe timeout before Excel launch; not an Excel result'
            (reports/'system-probes.stdout.log').write_text(decode(error.stdout))
            (reports/'system-probes.stderr.log').write_text(decode(error.stderr))
            raise
        (reports/'system-probes.stdout.log').write_text(checked.stdout)
        (reports/'system-probes.stderr.log').write_text(checked.stderr)
        checked.check_returncode()
        groups = {}
        current = None
        for line in checked.stdout.splitlines():
            row = line.split('\t')
            if row[0] in ('LIBRARY_LOADED', 'LIBRARY_FAILED', 'LIBRARY_PREFLIGHT') and len(row) >= 2:
                if row[1] in groups:
                    raise ValueError('Duplicate runtime library result')
                current = {'loaded': row[0] == 'LIBRARY_LOADED', 'found': [], 'missing': [], 'error': row[2:], 'images': []}
                if row[0] == 'LIBRARY_PREFLIGHT':
                    current['preflight'] = int(row[2])
                groups[row[1]] = current
            elif current is not None and row[0] == 'IMAGE' and len(row) == 3:
                current['images'].append({'path': row[1], 'platform': int(row[2])})
            elif current is not None and row[0] in ('FOUND', 'MISSING') and len(row) >= 2:
                current['found' if row[0] == 'FOUND' else 'missing'].append(row[1])
            else:
                raise ValueError('Unexpected runtime probe output: '+line)
        if set(groups) != {entry['target'] for entry in path_entries}:
            raise ValueError('Incomplete library probe batch')
        mapping = {}
        report['runtime_symbol_audits'] = []
        for entry in path_entries:
            audited = groups[entry['target']]
            names = [name.removeprefix('_') for name in graph['system_imports'].get(entry['original'], [])]
            if audited['loaded']:
                if set(audited['found']+audited['missing']) != set(names) or len(audited['found'])+len(audited['missing']) != len(names):
                    raise ValueError('Incomplete runtime symbol audit')
                if entry.get('probe_symbol') and entry['probe_symbol'] not in audited['found']:
                    raise ValueError('Previously confirmed counterpart export disappeared')
                if entry.get('map_eligible', True):
                    mapping[entry['original']] = entry['target']
            report['runtime_symbol_audits'].append({'original': entry['original'], 'target': entry['target'],
                'runtime_loaded': audited['loaded'], 'required_count': len(names),
                'found_count': len(audited['found']), 'missing': audited['missing'], 'load_error': audited['error'],
                'images': audited['images'], 'mapping_permitted': entry.get('map_eligible', True),
                'link_preflight': audited.get('preflight'), 'symbols_queried': audited['loaded'],
                'scope': 'SDK-absent preflight only' if not entry.get('map_eligible', True) else 'Runtime export lookup only; no API behavior, device availability or ABI guarantee'})
        # Gate the experimental private-provider bridge on this exact runtime,
        # before any Microsoft process starts. Only context/realm ownership is
        # exercised; no credentials or authentication exchange is attempted.
        contract = destination/'kerberos-contract-probe'
        run('xcrun', 'clang', '-target', 'arm64-apple-ios18.0-simulator', '-isysroot', sdk,
            '-fobjc-arc', '-fmodules', '-Wall', '-Wextra', '-Werror', '-I'+str(root/'shim'),
            root/'tests/kerberos_contracts.m', root/'shim/ExcelKerberos.m', root/'shim/ExcelShim.m',
            '-framework', 'Foundation', '-framework', 'GSS', '-Wl,-export_dynamic', '-o', contract)
        run('codesign', '--force', '--sign', '-', contract)
        contract_path = reports/'kerberos-forwarding-contracts.json'
        checked_contract = subprocess.run(['xcrun', 'simctl', 'spawn', udid, str(contract), str(contract_path)],
                                          text=True, capture_output=True, timeout=120)
        (reports/'kerberos-contract.stdout.log').write_text(checked_contract.stdout)
        (reports/'kerberos-contract.stderr.log').write_text(checked_contract.stderr)
        checked_contract.check_returncode()
        contracts = json.loads(contract_path.read_text())
        legacy = json.loads((root/'docs/evidence/kerberos-native-baseline.json').read_text())
        for key in ('oid_base64', 'oid_length', 'oid_struct_size', 'oid_elements_offset'):
            if contracts[key] != legacy[key]:
                raise ValueError('Kerberos OID legacy ABI changed: '+key)
        if not contracts['context_allocated_and_freed'] or not contracts['provider']['ready'] or contracts['provider']['expected_platform'] != 7:
            raise ValueError('Kerberos forwarding contract failed on this runtime')
        if contracts['credentials_used'] or contracts['authentication_attempted'] or contracts['excel_executed']:
            raise ValueError('Provider test exceeds isolated no-credentials contract scope')
        report['kerberos_forwarding_contracts'] = contracts
        result['system_path_modifications'] = []
        result['verified_system_path_mapping'] = mapping
        for image in result['images']:
            binary = destination/image['path']
            changed, events = rewrite_load_paths(binary.read_bytes(), mapping)
            if events:
                binary.write_bytes(changed)
                result['system_path_modifications'].append({'path': image['path'], 'events': events})
        result['optional_load_modifications'] = []
        if args.optional_frameworks:
            policy = json.loads(args.optional_frameworks.read_text())
            allowed = '/System/Library/Frameworks/ExceptionHandling.framework/Versions/A/ExceptionHandling'
            selected = set()
            for entry in policy:
                original = entry['original']
                if original != allowed or original in selected or not entry.get('observed_failure_run') or not entry.get('absence_preflight_run'):
                    raise ValueError('Optional framework needs its own explicit evidence-based policy')
                if graph['system_imports'].get(original):
                    raise ValueError('Optional framework has recorded direct imports')
                if any(name in graph['closure_objc_selectors'] for name in ('defaultExceptionHandler','setExceptionHandlingMask:','setExceptionHangingMask:')):
                    raise ValueError('Recorded exception-monitoring selectors require investigation')
                canonical = re.sub(r'/Versions/[^/]+', '', original)
                evidence = groups.get(canonical)
                if not evidence or evidence.get('preflight') != 0:
                    raise ValueError('Optional diagnostics experiment requires same-runtime failed counterpart preflight')
                selected.add(original)
            for image in result['images']:
                binary = destination/image['path']
                changed, events = weaken_unused_loads(binary.read_bytes(), selected)
                if events:
                    binary.write_bytes(changed)
                    result['optional_load_modifications'].append({'path': image['path'], 'events': events})
            result['optional_framework_policy'] = policy
        (reports/'real-loader-transform.json').write_text(json.dumps(result, indent=2)+'\n')
        # Only the verified startup closure is executable. No installer scripts,
        # privileged helpers, authentication or activation workarounds are run.
        for image in result['images']:
            binary = destination/image['path']
            run('codesign', '--force', '--sign', '-', binary)
            run('codesign', '--verify', '--strict', binary)
        executable = destination/'Contents/MacOS/Microsoft Excel'
        env = dict(os.environ)
        env['SIMCTL_CHILD_DYLD_PRINT_LIBRARIES'] = '1'
        env['SIMCTL_CHILD_DYLD_PRINT_RPATHS'] = '1'
        started = time.monotonic()
        with (reports/'real-loader.stdout.log').open('w') as stdout, (reports/'real-loader.stderr.log').open('w') as stderr:
            process = subprocess.Popen(['xcrun', 'simctl', 'spawn', udid, str(executable)],
                                       env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                report['returncode'] = process.wait(timeout=120)
                report['timed_out'] = False
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
                report['returncode'] = process.returncode
                report['timed_out'] = True
        report['elapsed_seconds'] = round(time.monotonic()-started, 2)
        stderr = (reports/'real-loader.stderr.log').read_text(errors='replace')
        mapped = re.findall(r'^dyld\[\d+\]: <[^>]+> (.+)$', stderr, re.MULTILINE)
        vendor_paths = {str(destination/image['path']) for image in result['images']}
        report['mapped_microsoft_image_count'] = sum(path in vendor_paths for path in mapped)
        report['mapped_compatibility_image_count'] = sum(path.startswith(str(destination)+'/Contents/') and path not in vendor_paths for path in mapped)
        missing_library = re.search(r'^dyld\[\d+\]: Library not loaded: (.+)$', stderr, re.MULTILINE)
        missing_symbol = re.search(r'(?:Symbol not found:|symbol not found[^:]*:)\s*(\S+)', stderr)
        if missing_library:
            report['first_failure'] = {'kind': 'library_not_loaded', 'name': missing_library[1]}
        elif missing_symbol:
            report['first_failure'] = {'kind': 'symbol_not_found', 'name': missing_symbol[1]}
        report['dyld_failure_present'] = any(s in stderr for s in ('Library not loaded:', 'Symbol not found:', 'incompatible platform', 'incompatible architecture'))
        report['status'] = 'Loader failure captured' if report['dyld_failure_present'] else 'Inspect logs; no Excel startup success inferred'
        print(stderr[-16000:], flush=True)
        try:
            logs = output('xcrun', 'simctl', 'spawn', udid, 'log', 'show', '--last', '2m', '--style', 'compact', '--predicate', 'process == "Microsoft Excel"', timeout=45)
            (reports/'real-loader-unified.log').write_text(logs[-1000000:])
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            report['secondary_log_error'] = str(error)
    finally:
        (reports/'real-loader-result.json').write_text(json.dumps(report, indent=2)+'\n')
        summary = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary:
            with open(summary, 'a') as file:
                file.write('### Real Excel loader investigation\n\n')
                file.write('Status: '+report.get('status', 'Infrastructure failure; inspect logs')+'\n\n')
                file.write('First failure: `'+report.get('first_failure', {}).get('name', 'See diagnostic reports')+'`\n\n')
                file.write('**Microsoft entry point and Excel initialization remain unconfirmed. No IPA produced.**\n')
        print(json.dumps(report, indent=2), flush=True)
        for operation in ('shutdown', 'delete'):
            try:
                subprocess.run(['xcrun', 'simctl', operation, udid], check=False, timeout=60)
            except subprocess.TimeoutExpired:
                print('Simulator cleanup timed out:', operation, flush=True)


if __name__ == '__main__':
    main()
