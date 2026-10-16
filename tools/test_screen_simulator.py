#!/usr/bin/env python3
"""Execute the real UIKit entry/screen adapter on an internal iPad simulator host.
No Microsoft payload, IPA or public test-app artifact is produced.
"""
import json
import os
import plistlib
import shutil
import subprocess
import time
from pathlib import Path


def run(*args, **kwargs):
    return subprocess.run(list(map(str,args)),check=True,text=True,**kwargs)


def output(*args):
    return subprocess.check_output(list(map(str,args)),text=True).strip()


def main():
    root=Path(__file__).resolve().parents[1]
    destination=root/'build/screen-simulator'
    if destination.exists():
        shutil.rmtree(destination)
    app=destination/'ScreenAdapterTests.app'
    app.mkdir(parents=True)
    reports=root/'reports'
    reports.mkdir(exist_ok=True)
    sdk=output('xcrun','--sdk','iphonesimulator','--show-sdk-path')
    run('python3',root/'tests/nib_fixture.py',app/'Desktop/Microsoft Excel.app/Contents')
    bundle_id='com.excelport.internal.screen-tests'
    info={'CFBundleIdentifier':bundle_id,'CFBundleExecutable':'ScreenAdapterTests',
          'CFBundleName':'Internal Screen Tests','CFBundleDisplayName':'Internal Screen Tests',
          'CFBundleVersion':'1','CFBundleShortVersionString':'1.0','CFBundlePackageType':'APPL',
          'CFBundleSupportedPlatforms':['iPhoneSimulator'],'MinimumOSVersion':'18.0','UIDeviceFamily':[2],
          'UIApplicationSceneManifest':{'UIApplicationSupportsMultipleScenes':False,'UISceneConfigurations':{}},
          'UILaunchScreen':{},'UISupportedInterfaceOrientations':['UIInterfaceOrientationPortrait','UIInterfaceOrientationLandscapeLeft','UIInterfaceOrientationLandscapeRight']}
    (app/'Info.plist').write_bytes(plistlib.dumps(info))
    sources=['shim/ExcelNibArchive.m','shim/ExcelAppKit.m','shim/ExcelShim.m','shim/ExcelScreen.m','shim/ExcelView.m','tests/simulator_screen_app.m']
    run('xcrun','clang','-target','arm64-apple-ios18.0-simulator','-isysroot',sdk,
        '-fobjc-arc','-fmodules','-Wall','-Wextra','-Werror','-Wno-unused-parameter',
        '-DEXCELSHIM_CONTRACT_TEST=1','-I'+str(root/'shim'),*[root/s for s in sources],
        '-framework','UIKit','-framework','Foundation','-framework','CoreGraphics','-o',app/'ScreenAdapterTests')
    run('codesign','--force','--sign','-',app)
    devices=json.loads(output('xcrun','simctl','list','devices','available','--json'))['devices']
    candidates=[]
    for runtime,items in devices.items():
        if 'iOS-' not in runtime:
            continue
        version=tuple(int(part) for part in runtime.rsplit('iOS-',1)[1].split('-'))
        if version[0]<18:
            continue
        for device in items:
            if 'iPad' in device['name'] and device.get('isAvailable',False):
                candidates.append((runtime,device,version))
    if not candidates:
        raise RuntimeError('No available iPad simulator runtime; cannot claim the UIKit runtime check passed')
    # Prefer the user's model family if installed, otherwise use an available iPad.
    candidates.sort(key=lambda x:('M4' not in x[1]['name'],'Pro' not in x[1]['name'],tuple(-v for v in x[2])))
    runtime,template,_=candidates[0]
    device_type=template.get('deviceTypeIdentifier')
    if not device_type:
        types=json.loads(output('xcrun','simctl','list','devicetypes','--json'))['devicetypes']
        device_type=next(t['identifier'] for t in types if t['name']==template['name'])
    udid=output('xcrun','simctl','create','ExcelScreen-'+os.environ.get('GITHUB_RUN_ID','local'),device_type,runtime)
    print('Using isolated simulator:',template['name'],runtime,flush=True)
    try:
        run('xcrun','simctl','boot',udid)
        run('xcrun','simctl','bootstatus',udid,'-b',timeout=240)
        run('xcrun','simctl','install',udid,app)
        container=Path(output('xcrun','simctl','get_app_container',udid,bundle_id,'data'))
        run('xcrun','simctl','launch',udid,bundle_id)
        result=container/'Documents/screen-simulator-result.json'
        deadline=time.monotonic()+60
        while time.monotonic()<deadline and not result.exists():
            time.sleep(0.25)
        if not result.exists():
            raise RuntimeError('Screen host produced no result after 60 seconds')
        report=json.loads(result.read_text())
        report['simulator_device']=template['name']
        report['runtime_identifier']=runtime
        (reports/'screen-simulator.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2),flush=True)
        if not report.get('passed'):
            raise RuntimeError('UIKit adapter test reported failure')
    except Exception:
        try:
            logs=output('xcrun','simctl','spawn',udid,'log','show','--last','2m','--style','compact','--predicate','process == "ScreenAdapterTests"')
            (reports/'screen-simulator-failure.log').write_text(logs[-1000000:])
            if 'container' in locals():
                for log in (container/'Documents').glob('*.log'):
                    shutil.copyfile(log,reports/('host-'+log.name))
        except Exception as secondary:
            print('Additional log retrieval failed:',secondary,flush=True)
        raise
    finally:
        subprocess.run(['xcrun','simctl','shutdown',udid],check=False)
        subprocess.run(['xcrun','simctl','delete',udid],check=False)


if __name__=='__main__':
    main()
