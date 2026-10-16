#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/compatibility
python3 tests/nib_fixture.py build/compatibility/Synthetic.app/Contents
CLANG="$(xcrun --find clang)"
COMMON=(-fobjc-arc -fmodules -Wall -Wextra -Werror -Wno-unused-parameter -Ishim)
MACSDK="$(xcrun --sdk macosx --show-sdk-path)"
"$CLANG" "${COMMON[@]}" -isysroot "$MACSDK" -DEXCELSHIM_CONTRACT_TEST=1 \
  shim/ExcelNibArchive.m shim/ExcelAppKit.m shim/ExcelShim.m shim/ExcelScreen.m shim/ExcelView.m tests/native_nib_tests.m \
  -framework Foundation -framework CoreGraphics -o build/compatibility/native-nib-tests
if [ "$#" -gt 0 ]; then
  build/compatibility/native-nib-tests build/compatibility/Synthetic.app/Contents "$@"
else
  build/compatibility/native-nib-tests build/compatibility/Synthetic.app/Contents
fi
SDK="$(xcrun --sdk iphoneos --show-sdk-path)"
# Compile the actual iOS bridge as a dylib; this is an internal check, not an IPA release.
"$CLANG" "${COMMON[@]}" -target arm64-apple-ios18.0 -isysroot "$SDK" \
  -dynamiclib shim/ExcelNibArchive.m shim/ExcelAppKit.m shim/ExcelShim.m shim/ExcelScreen.m shim/ExcelView.m \
  -framework Foundation -framework UIKit -framework CoreGraphics -install_name @rpath/libExcelShim.dylib \
  -o build/compatibility/libExcelShim.dylib
codesign --force --sign - build/compatibility/libExcelShim.dylib
codesign --verify --strict build/compatibility/libExcelShim.dylib
nm -gU build/compatibility/libExcelShim.dylib > build/compatibility/exports.txt
python3 - <<'PY'
from pathlib import Path
symbols=Path('build/compatibility/exports.txt').read_text()
for name in ['_NSApplicationMain','_OBJC_CLASS_$_NSScreen','_OBJC_CLASS_$_NSView','_OBJC_CLASS_$_NSApplication','_OBJC_CLASS_$_NSResponder','_OBJC_CLASS_$_NSDocumentController','_OBJC_CLASS_$_NSFontManager']:
    if name not in symbols:raise SystemExit('Missing required compatibility export: '+name)
print('iOS arm64 compatibility exports verified. No runnable Excel IPA produced.')
PY
