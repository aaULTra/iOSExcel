#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/screen
python3 - <<'PY'
import gzip,json
from pathlib import Path
all_classes=json.loads(gzip.decompress(Path('docs/evidence/appkit-contracts-macos-15.json.gz').read_bytes()))
cls=next(c for c in all_classes['classes'] if c['name']=='NSScreen')
instance={'frame','visibleFrame','backingScaleFactor','localizedName','deviceDescription','convertRectToBacking:','convertRectFromBacking:'}
expected={'instance_methods':[m for m in cls['instance_methods'] if m['selector'] in instance], 'class_methods':[m for m in cls['class_methods'] if m['selector'] in {'screens','mainScreen'}]}
assert len(expected['instance_methods'])==7 and len(expected['class_methods'])==2
Path('build/screen/expected-abi.json').write_text(json.dumps(expected))
PY
xcrun clang -target arm64-apple-macos11.0 -isysroot "$(xcrun --sdk macosx --show-sdk-path)" \
  -fobjc-arc -fmodules -Wall -Wextra -Werror -Wno-unused-parameter -Ishim \
  shim/ExcelScreen.m shim/ExcelShim.m tests/native_screen_tests.m \
  -framework Foundation -framework CoreGraphics -o build/screen/native-screen-tests
build/screen/native-screen-tests build/screen/expected-abi.json build/screen/native-report.json
