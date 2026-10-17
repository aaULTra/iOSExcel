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
from excel_retarget import rewrite_load_paths
from loader_plan import load_json, plan, stage


def output(*args):
    return subprocess.check_output(list(map(str, args)), text=True).strip()


def run(*args):
    subprocess.run(list(map(str, args)), check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('app', type=Path)
    ap.add_argument('--system-path-map', type=Path)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    reports = root/'reports'
    reports.mkdir(exist_ok=True)
    destination = root/'private/real-loader'
    graph = load_json(root/'docs/evidence/dependencies-16.55.json.gz')
    result = plan(args.app, load_json(root/'docs/evidence/excel-16.55.json.gz'), graph, platform=7)
    stage(args.app, destination, result)
    path_entries = json.loads(args.system_path_map.read_text()) if args.system_path_map else []
    mapping = {}
    for entry in path_entries:
        old, new = entry['original'], entry['target']
        if old in mapping or not old.startswith('/System/Library/Frameworks/') or not new.startswith('/System/Library/Frameworks/') or '..' in Path(new).parts:
            raise ValueError('Unexpected system library path mapping')
        if not entry.get('observed_failure_run') or not entry.get('probe_symbol'):
            raise ValueError('Path mapping needs an observed failure and a runtime probe')
        mapping[old] = new
    result['system_path_modifications'] = []
    for image in result['images']:
        binary = destination/image['path']
        changed, events = rewrite_load_paths(binary.read_bytes(), mapping)
        if events:
            binary.write_bytes(changed)
            result['system_path_modifications'].append({'path': image['path'], 'events': events})
    (reports/'real-loader-transform.json').write_text(json.dumps(result, indent=2)+'\n')
    frameworks = destination/'Contents/Frameworks'
    sdk = output('xcrun', '--sdk', 'iphonesimulator', '--show-sdk-path')
    for entry in path_entries:
        if not Path(str(Path(sdk)/entry['target'].lstrip('/'))+'.tbd').is_file():
            raise ValueError('Counterpart missing from Simulator SDK: '+entry['target'])
    probe = destination/'probe-system-library'
    run('xcrun', 'clang', '-target', 'arm64-apple-ios18.0-simulator', '-isysroot', sdk,
        '-Wall', '-Wextra', '-Werror', root/'tests/loader/probe_system_library.c', '-o', probe)
    run('codesign', '--force', '--sign', '-', probe)
    shim = frameworks/'libExcelShim.dylib'
    sources = ['ExcelNibArchive.m', 'ExcelAppKit.m', 'ExcelShim.m', 'ExcelScreen.m', 'ExcelView.m']
    run('xcrun', 'clang', '-target', 'arm64-apple-ios18.0-simulator', '-isysroot', sdk,
        '-fobjc-arc', '-fmodules', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
        '-I'+str(root/'shim'), '-dynamiclib', *[root/'shim'/s for s in sources],
        '-framework', 'UIKit', '-framework', 'Foundation', '-framework', 'CoreGraphics',
        '-install_name', '@rpath/libExcelShim.dylib', '-o', shim)
    run('codesign', '--force', '--sign', '-', shim)
    for facade in result['facades']:
        build_one(shim, frameworks/Path(facade['install_name']).name,
                  facade['install_name'], facade['required_compatibility_version'], 'simulator')
    # Only the verified startup closure is executable. No installer scripts,
    # privileged helpers, authentication or activation workarounds are run.
    for image in result['images']:
        binary = destination/image['path']
        run('codesign', '--force', '--sign', '-', binary)
        run('codesign', '--verify', '--strict', binary)
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
        report['system_library_probes'] = []
        for entry in path_entries:
            try:
                checked = subprocess.run(['xcrun', 'simctl', 'spawn', udid, str(probe), entry['target'], entry['probe_symbol']],
                                         text=True, capture_output=True, timeout=180)
            except subprocess.TimeoutExpired as error:
                def decode(value):
                    return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
                report['status'] = 'Infrastructure/probe timeout before Excel launch; not an Excel result'
                report['system_library_probes'].append({'target': entry['target'], 'timed_out': True,
                    'stdout': decode(error.stdout), 'stderr': decode(error.stderr)})
                raise
            report['system_library_probes'].append({'target': entry['target'], 'symbol': entry['probe_symbol'],
                                                   'returncode': checked.returncode, 'stdout': checked.stdout, 'stderr': checked.stderr})
            print(checked.stdout, checked.stderr, flush=True)
            checked.check_returncode()
        report['runtime_symbol_audits'] = []
        for entry in path_entries:
            # dlsym accepts C names without Mach-O's leading underscore. This
            # queries exports only; no Microsoft or Security function is called.
            required = graph['system_imports'].get(entry['original'], [])
            names = [s.removeprefix('_') for s in required]
            audited = subprocess.run(['xcrun', 'simctl', 'spawn', udid, str(probe), entry['target'], '--audit', *names],
                                     text=True, capture_output=True, timeout=120)
            audited.check_returncode()
            rows = [line.split('\t') for line in audited.stdout.splitlines()]
            found = [row[1] for row in rows if len(row) == 3 and row[0] == 'FOUND']
            missing = [row[1] for row in rows if len(row) == 2 and row[0] == 'MISSING']
            if set(found+missing) != set(names) or len(found)+len(missing) != len(names):
                raise ValueError('Incomplete runtime export audit')
            report['runtime_symbol_audits'].append({'original': entry['original'], 'target': entry['target'],
                'required_count': len(names), 'found_count': len(found), 'missing': missing,
                'raw_output': audited.stdout, 'scope': 'Export lookup only; no API behavior or ABI guarantee'})
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
        report['mapped_microsoft_image_count'] = sum(path.startswith(str(destination)+'/Contents/') for path in mapped)
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
            logs = output('xcrun', 'simctl', 'spawn', udid, 'log', 'show', '--last', '2m', '--style', 'compact', '--predicate', 'process == "Microsoft Excel"')
            (reports/'real-loader-unified.log').write_text(logs[-1000000:])
        except subprocess.CalledProcessError as error:
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
        subprocess.run(['xcrun', 'simctl', 'shutdown', udid], check=False)
        subprocess.run(['xcrun', 'simctl', 'delete', udid], check=False)


if __name__ == '__main__':
    main()
