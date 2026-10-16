#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/view
python3 - <<'PY'
import gzip,json
from pathlib import Path
metadata=json.loads(gzip.decompress(Path('docs/evidence/appkit-contracts-macos-15.json.gz').read_bytes()))
cls=next(c for c in metadata['classes'] if c['name']=='NSView')
# Explicit implemented contract list; no generic signature generation.
names={'init','initWithFrame:','frame','setFrame:','bounds','setBounds:','superview','subviews','window','isFlipped','isHidden','setHidden:','needsDisplay','setNeedsDisplay:','needsLayout','setNeedsLayout:','setFrameOrigin:','setFrameSize:','setBoundsOrigin:','setBoundsSize:','addSubview:','removeFromSuperview','isDescendantOf:','convertPoint:toView:','convertPoint:fromView:','convertRect:toView:','convertRect:fromView:','viewWillMoveToSuperview:','viewDidMoveToSuperview','drawRect:','layout','layoutSubtreeIfNeeded'}
selected=[m for m in cls['instance_methods'] if m['selector'] in names]
assert {m['selector'] for m in selected}==names
Path('build/view/expected-abi.json').write_text(json.dumps(selected))
PY
xcrun clang -target arm64-apple-macos11.0 -isysroot "$(xcrun --sdk macosx --show-sdk-path)" \
  -fobjc-arc -fmodules -Wall -Wextra -Werror -Wno-unused-parameter -Ishim \
  shim/ExcelView.m shim/ExcelAppKit.m shim/ExcelNibArchive.m shim/ExcelShim.m shim/ExcelScreen.m tests/native_view_tests.m \
  -framework Foundation -framework CoreGraphics -o build/view/native-view-tests
build/view/native-view-tests build/view/expected-abi.json build/view/native-report.json
