#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
SDK="$(xcrun --sdk iphoneos --show-sdk-path)"
CLANG="$(xcrun --find clang)"
OUT="${OUT:-build/probe}"
APP="$OUT/Payload/ExcelPortProbe.app"
[ ! -e "$OUT" ] || { echo 'Output already exists; choose a fresh OUT directory'; exit 1; }
mkdir -p "$APP/Frameworks"
COMMON=(-target arm64-apple-ios18.0 -isysroot "$SDK" -fobjc-arc -fmodules -Wall -Wextra -Werror -Wno-unused-parameter -Ishim)
"$CLANG" "${COMMON[@]}" -dynamiclib shim/ExcelShim.m -framework Foundation -install_name @rpath/libExcelShim.dylib -o "$APP/Frameworks/libExcelShim.dylib"
"$CLANG" "${COMMON[@]}" app/main.m -framework UIKit -framework Foundation -L"$APP/Frameworks" -lExcelShim -Wl,-rpath,@executable_path/Frameworks -o "$APP/ExcelPortProbe"
cp app/Info.plist "$APP/Info.plist"
codesign --force --sign - "$APP/Frameworks/libExcelShim.dylib"
codesign --force --sign - --entitlements app/entitlements.plist "$APP"
codesign --verify --deep --strict "$APP"
(cd "$OUT" && zip -qry ExcelPortProbe-unsigned.ipa Payload)
echo "Probe only; Excel is NOT included or loaded: $OUT/ExcelPortProbe-unsigned.ipa"
