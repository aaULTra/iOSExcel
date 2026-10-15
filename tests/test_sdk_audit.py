import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
 from audit_sdk import audit
except ImportError:audit=None
@unittest.skipIf(audit is None,'PyYAML optional; install it to exercise SDK stub parser')
class SDKAuditTest(unittest.TestCase):
 def test_ios_targets_objc_and_reexport(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'usr/lib').mkdir(parents=True)
   (root/'usr/lib/base.tbd').write_text('''--- !tapi-tbd
tbd-version: 4
targets: [ arm64-ios, arm64-ios-simulator ]
install-name: /usr/lib/base.dylib
exports:
  - targets: [ arm64-ios ]
    symbols: [ _available ]
    objc-classes: [ Test ]
  - targets: [ arm64-ios-simulator ]
    symbols: [ _simulatorOnly ]
reexported-libraries:
  - targets: [ arm64-ios ]
    libraries: [ /usr/lib/child.dylib ]
''')
   (root/'usr/lib/child.tbd').write_text('''--- !tapi-tbd
tbd-version: 4
targets: [ arm64-ios ]
install-name: /usr/lib/child.dylib
exports:
  - targets: [ arm64-ios ]
    symbols: [ _child ]
''')
   r=audit(root,{'system_imports':{'/usr/lib/base.dylib':['_available','_child','_OBJC_CLASS_$_Test','_simulatorOnly','_missing']}})['libraries'][0]
   self.assertEqual(r['declared_count'],3);self.assertEqual(r['not_found_in_parsed_exports'],['_missing','_simulatorOnly']);self.assertEqual(r['unresolved'],[])
 def test_absent_stub_explicit(self):
  with tempfile.TemporaryDirectory() as t:
   r=audit(Path(t),{'system_imports':{'/usr/lib/absent.dylib':['_x']}})['libraries'][0]
   self.assertTrue(r['unresolved']);self.assertEqual(r['declared_count'],0)
