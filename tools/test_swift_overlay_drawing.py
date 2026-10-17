#!/usr/bin/env python3
"""Compare the actual typed Swift method against genuine AppKit offscreen pixels.
No Microsoft code, activation, windows or physical-device execution is involved.
"""
import json
import os
import subprocess
from pathlib import Path
from test_swift_overlay import build_overlay, run


def compare(expected, actual, label):
    if len(expected['cases']) != 96 or len(actual['cases']) != 96:
        raise RuntimeError('Expected exactly 96 drawing cases')
    for index, (native, candidate) in enumerate(zip(expected['cases'], actual['cases'])):
        if native != candidate:
            keys = [key for key in native if native[key] != candidate.get(key)]
            raise RuntimeError(f'{label}: native drawing mismatch case {index}: {keys}')


def main():
    root = Path(__file__).resolve().parents[1]
    reports = root/'reports'
    expected = json.loads((reports/'swift-overlay-native-drawing.json').read_text())
    executables = {}
    for platform, sdk_name, triple in [('macos','macosx','arm64-apple-macos11.0'),
                                      ('simulator','iphonesimulator','arm64-apple-ios18.0-simulator')]:
        build = root/'build'/('swift-drawing-'+platform)
        library, _ = build_overlay(root, build, platform, test_context=platform=='macos')
        executable = build/'drawing-client'
        sdk = run('xcrun','--sdk',sdk_name,'--show-sdk-path').strip()
        run('xcrun','swiftc','-sdk',sdk,'-target',triple,'-D','EXCEL_OVERLAY_DRAWING_TEST',
            '-I',str(build),'-I',str(root/'experiments/swift-appkit'),'-L',str(build),
            '-lExcelSwiftAppKit','-Xlinker','-rpath','-Xlinker',str(build),
            str(root/'tools/swift_overlay_drawing_values.swift'),'-o',str(executable))
        for binary in [library,executable]:
            run('codesign','--force','--sign','-',str(binary))
            run('codesign','--verify','--strict',str(binary))
        executables[platform] = executable
    mac_result = reports/'swift-overlay-macos-drawing.json'
    run(str(executables['macos']),str(mac_result))
    compare(expected,json.loads(mac_result.read_text()),'Mac test-context backend')
    devices = json.loads(run('xcrun','simctl','list','devices','available','--json'))['devices']
    candidates = [(runtime,device) for runtime,items in devices.items() if 'iOS-' in runtime
                  for device in items if device.get('isAvailable') and 'iPad' in device['name']]
    candidates.sort(key=lambda row:('M4' not in row[1]['name'],tuple(-int(v) for v in row[0].rsplit('iOS-',1)[1].split('-'))))
    if not candidates:
        raise RuntimeError('No iPad Simulator available')
    runtime, template = candidates[0]
    dtype = template.get('deviceTypeIdentifier')
    if not dtype:
        types = json.loads(run('xcrun','simctl','list','devicetypes','--json'))['devicetypes']
        dtype = next(row['identifier'] for row in types if row['name']==template['name'])
    udid = run('xcrun','simctl','create','SwiftDrawing-'+os.environ.get('GITHUB_RUN_ID','local'),dtype,runtime).strip()
    try:
        run('xcrun','simctl','boot',udid)
        subprocess.run(['xcrun','simctl','bootstatus',udid,'-b'],check=True,timeout=240)
        result = reports/'swift-overlay-ios-drawing.json'
        proc = subprocess.run(['xcrun','simctl','spawn',udid,str(executables['simulator']),str(result)],
                              text=True,capture_output=True,timeout=120)
        (reports/'swift-overlay-drawing.stderr.log').write_text(proc.stderr)
        if proc.returncode:
            raise RuntimeError('iOS drawing client failed: '+proc.stderr[-2000:])
        compare(expected,json.loads(result.read_text()),'iOS UIKit current-context backend')
        (reports/'swift-overlay-drawing-validation.json').write_text(json.dumps({
            'native_cases':96,'mac_pixel_and_state_cases_matched':96,'ios_pixel_and_state_cases_matched':96,
            'operations':[1,2],'nonfinite_or_other_operations_supported':False,
            'device':template['name'],'runtime':runtime,'physical_device_executed':False,
            'microsoft_executed':False,'microsoft_overlay_redirected':False,
            'scope':'Offscreen finite rectangle copy/sourceOver only; no NSGraphicsContext or desktop UI implementation'
        },indent=2)+'\n')
    finally:
        for action in ['shutdown','delete']:
            try:
                subprocess.run(['xcrun','simctl',action,udid],timeout=60,check=False,capture_output=True)
            except subprocess.TimeoutExpired:
                print('Simulator cleanup timeout:',action)


if __name__=='__main__':
    main()
