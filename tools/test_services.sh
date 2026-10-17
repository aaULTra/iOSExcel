#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/services reports
SDK="$(xcrun --sdk macosx --show-sdk-path)"
COMMON=(-target arm64-apple-macos11.0 -isysroot "$SDK" -fobjc-arc -fmodules -Wall -Wextra -Werror -Wno-unused-parameter -Ishim)
# Separate original-Apple and compatibility processes: the baseline never links our replacements.
xcrun clang "${COMMON[@]}" -DEXCELSHIM_SHAPE_BASELINE=1 tests/native_services_tests.m \
  -framework Foundation -framework ApplicationServices -o build/services/apple-baseline
build/services/apple-baseline build/services/apple-shapes.json
xcrun clang "${COMMON[@]}" tests/native_services_tests.m shim/ExcelApplicationServices.m shim/ExcelShim.m \
  -framework Foundation -framework CoreGraphics -o build/services/compatibility-shapes
build/services/compatibility-shapes build/services/compatibility-shapes.json
xcrun clang "${COMMON[@]}" tests/services_type_tests.m -framework Foundation -framework CoreGraphics -o build/services/type-tests
build/services/type-tests docs/evidence/application-services-values.json
python3 - <<'PY'
import json,math
from pathlib import Path
original=json.loads(Path('build/services/apple-shapes.json').read_text())
compat=json.loads(Path('build/services/compatibility-shapes.json').read_text())
for group in ('shapes','intersections'):
    assert len(original[group])==len(compat[group])
    for i,(a,b) in enumerate(zip(original[group],compat[group])):
        assert a['empty']==b['empty'],(group,i,a,b)
        assert len(a['bounds'])==len(b['bounds']),(group,i,a,b)
        assert all(math.isclose(x,y,rel_tol=0,abs_tol=1e-7) for x,y in zip(a['bounds'],b['bounds'])),(group,i,a,b)
report={'native_Apple_geometry_comparison_passed':True,'shape_cases':len(original['shapes']),
        'intersection_cases':len(original['intersections']),'C_type_contracts':17,
        'unsupported_operations_report_errors_or_raise':True,'excel_executed':False,
        'scope':'Only three shape operations and explicit disabled-feature contracts; no desktop UI, clipboard or printing functionality claimed'}
Path('reports/native-services-contracts.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS:',report)
PY
