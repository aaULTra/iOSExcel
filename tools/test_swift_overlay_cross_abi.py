#!/usr/bin/env python3
"""Run own Mac-compiled Swift client on iPad Simulator against typed iOS overlay.
This fixture contains no Microsoft payload and does not claim Office compiler ABI,
rendering, installed-app lifecycle, activation or physical-device compatibility.
"""
import json
import os
import re
import subprocess
from pathlib import Path
from test_swift_overlay import build_overlay
from build_facades import build_one
from excel_retarget import retarget
from loader_plan import payload_hashes
from macho import arm64, commands, inspect, DYLIBS, string, unpack, version


def call(*args, timeout=180):
    return subprocess.check_output(list(map(str, args)), text=True, timeout=timeout).strip()


def main():
    root = Path(__file__).resolve().parents[1]
    build = root/'build/swift-overlay-cross'
    build.mkdir(parents=True, exist_ok=True)
    reports = root/'reports'
    reports.mkdir(exist_ok=True)
    sdk = call('xcrun', '--sdk', 'iphonesimulator', '--show-sdk-path')
    macsdk = call('xcrun', '--sdk', 'macosx', '--show-sdk-path')
    native = build/'mac-client'
    call('xcrun', 'swiftc', '-sdk', macsdk, '-target', 'arm64-apple-macos11.0',
         '-Xlinker', '-rpath', '-Xlinker', '@executable_path',
         root/'tools/swift_overlay_client.swift', '-o', native)
    call(native, reports/'swift-overlay-original-mac-client.json')
    before = arm64(native.read_bytes())
    original = inspect(before)
    versions = {}
    for command, offset, size in commands(before):
        if command in DYLIBS:
            dep = string(before,offset+unpack('<I',before,offset+8)[0],offset+size)
            versions[dep] = unpack('<I',before,offset+20)[0]
    required_version = version(versions.get('/usr/lib/swift/libswiftAppKit.dylib',0))
    library, names = build_overlay(root, build, 'simulator', required_version)
    device_library, _ = build_overlay(root, root/'build/swift-overlay-device', 'ios', required_version)
    if inspect(device_library.read_bytes())['build_versions'][0]['platform'] != 2:
        raise RuntimeError('Device overlay must be platform 2')
    call('codesign','--force','--sign','-',device_library)
    call('codesign','--verify','--strict',device_library)
    (reports/'swift-overlay-device-build.json').write_text(json.dumps({'platform':2,
        'required_version':required_version,'required_exports_verified':names,'signature_verified':True,
        'device_execution':False,'microsoft_executed':False},indent=2)+'\n')

    mapping = {'/usr/lib/swift/libswiftAppKit.dylib':'@rpath/libExcelSwiftAppKit.dylib'}
    appkit = '/System/Library/Frameworks/AppKit.framework/Versions/C/AppKit'
    (reports/'swift-overlay-mac-caller-imports.json').write_text(json.dumps(original,indent=2)+'\n')
    if any(row['library'] == appkit and row['name'] not in names for row in original['undefined']):
        raise RuntimeError('Own fixture imports an AppKit API outside the measured Swift exports')
    requirement = []
    for command, offset, size in commands(before):
        if command not in DYLIBS:
            continue
        name = string(before, offset+unpack('<I',before,offset+8)[0], offset+size)
        if name == appkit:
            requirement.append(version(unpack('<I',before,offset+20)[0]))
    if len(requirement) > 1:
        raise RuntimeError('Unexpected duplicate AppKit dependency in own fixture')
    if requirement:
        build_one(library, build/'ExcelAppKit.dylib', '@rpath/ExcelAppKit.dylib', requirement[0], 'simulator')
        mapping[appkit] = '@rpath/ExcelAppKit.dylib'
    for dep in original['dylibs']:
        path = dep['path']
        if path in mapping or not path.startswith('/System/Library/Frameworks/'):
            continue
        canonical = re.sub(r'/Versions/[^/]+/', '/', path)
        if canonical != path:
            stub = Path(sdk)/(canonical.lstrip('/')+'.tbd')
            if not stub.is_file():
                raise RuntimeError('No iOS SDK declaration for fixture dependency: '+canonical)
            mapping[path] = canonical
    after, events = retarget(before, '18.0', '18.5', mapping, platform=7)
    if payload_hashes(before) != payload_hashes(after):
        raise RuntimeError('Own Mac fixture code/linkedit changed before signing')
    converted = build/'retargeted-mac-client'
    converted.write_bytes(after)
    converted.chmod(0o755)
    ios = build/'ios-client'
    call('xcrun', 'swiftc', '-sdk', sdk, '-target', 'arm64-apple-ios18.0-simulator',
         '-I', build, '-I', root/'experiments/swift-appkit', '-L', build, '-lExcelSwiftAppKit',
         '-Xlinker', '-rpath', '-Xlinker', '@executable_path',
         root/'tools/swift_overlay_client.swift', '-o', ios)
    for binary in [library, converted, ios]:
        if inspect(binary.read_bytes())['build_versions'][0]['platform'] != 7:
            raise RuntimeError('Fixture library/process must be Simulator platform 7')
        call('codesign', '--force', '--sign', '-', binary)
        call('codesign', '--verify', '--strict', binary)
    (reports/'swift-overlay-fixture-transform.json').write_text(json.dumps({'before':original,
        'modifications':events,'code_linkedit_unchanged_before_signing':True,
        'required_swift_exports':names,'microsoft_payload':False},indent=2)+'\n')
    devices = json.loads(call('xcrun','simctl','list','devices','available','--json',timeout=120))['devices']
    candidates = [(runtime,device,tuple(map(int,runtime.rsplit('iOS-',1)[1].split('-'))))
                  for runtime,items in devices.items() if 'iOS-' in runtime
                  for device in items if device.get('isAvailable') and 'iPad' in device['name']]
    candidates = [row for row in candidates if row[2][0]>=18]
    candidates.sort(key=lambda row:('M4' not in row[1]['name'],'Pro' not in row[1]['name'],tuple(-v for v in row[2])))
    if not candidates:
        raise RuntimeError('No iPad Simulator available')
    runtime, template, _ = candidates[0]
    dtype = template.get('deviceTypeIdentifier')
    if not dtype:
        types = json.loads(call('xcrun','simctl','list','devicetypes','--json'))['devicetypes']
        dtype = next(row['identifier'] for row in types if row['name']==template['name'])
    udid = call('xcrun','simctl','create','SwiftOverlay-'+os.environ.get('GITHUB_RUN_ID','local'),dtype,runtime)
    expected = json.loads((reports/'swift-overlay-original-mac-client.json').read_text())
    results = []
    try:
        call('xcrun','simctl','boot',udid)
        call('xcrun','simctl','bootstatus',udid,'-b',timeout=240)
        for name, executable in [('ios',ios),('mac-retargeted',converted)]:
            result = reports/f'swift-overlay-{name}-client.json'
            for mode in ['values','--draw','--invalid']:
                arguments = [] if mode=='values' else [mode]
                proc = subprocess.run(['xcrun','simctl','spawn',udid,str(executable),str(result),*arguments],
                                      text=True,capture_output=True,timeout=120)
                (reports/f'swift-overlay-{name}-{mode.lstrip("-")}.stderr.log').write_text(proc.stderr)
                if mode=='values':
                    if proc.returncode or not result.is_file():
                        raise RuntimeError(name+' fixture failed before getter report: '+proc.stderr[-2000:])
                    if json.loads(result.read_text()) != expected:
                        raise RuntimeError(name+' Swift getter/layout cross-ABI mismatch')
                elif mode=='--draw':
                    found = re.search(r'SWIFT_OVERLAY_DRAW ([^\n]+)',proc.stderr)
                    if proc.returncode==0 or not found or list(map(float,found[1].split())) != [1.25,2.5,20,30,2]:
                        raise RuntimeError(name+' drawing call did not reach typed argument-preserving failure')
                elif proc.returncode==0 or 'IndexPath.item requires a measured two-component path' not in proc.stderr:
                    raise RuntimeError(name+' invalid path did not fail explicitly')
                results.append({'client':name,'mode':mode,'returncode':proc.returncode,'expected_behavior_verified':True})
        (reports/'swift-overlay-cross-abi.json').write_text(json.dumps({'device':template['name'],'runtime':runtime,
            'cases':results,'five_getter_cases_per_client':True,'drawing_arguments_preserved_before_explicit_abort':True,
            'drawing_implemented':False,'device_overlay_compiled_and_signed_only':True,'office_compiler_abi_verified':False,'microsoft_executed':False},indent=2)+'\n')
    finally:
        for action in ['shutdown','delete']:
            try:
                subprocess.run(['xcrun','simctl',action,udid],timeout=60,check=False,capture_output=True)
            except subprocess.TimeoutExpired:
                print('Secondary simulator cleanup timeout:',action,flush=True)
    print('Own native-iOS and retargeted-Mac Swift client contracts passed; no Excel startup inferred')


if __name__=='__main__':
    main()
