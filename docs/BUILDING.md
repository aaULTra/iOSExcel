# Building and reproducing evidence

Requires Python 3.10+ (stdlib only) for extraction, inventory and retargeting.
No installer scripts are executed. Microsoft packages remain outside source control.
The attached VL Serializer is NOT an Excel application installer and is never uploaded.

```
python3 -m unittest discover -s tests -v
python3 tools/extract_pkg.py /path/to/Microsoft_Excel_16.55.21111400_Updater.pkg private/extracted
python3 tools/analyze_excel.py 'private/extracted/Microsoft Excel.app' --output private/analysis.json
python3 tools/excel_retarget.py 'private/extracted/Microsoft Excel.app' private/retargeted.app --log private/modifications.json
```

The recursive retargeter deliberately fails if any embedded Mach-O has no plain arm64
slice, legacy metadata, encryption, malformed commands or duplicate mapped imports.
An optional --map JSON is an EXACT old-path -> new-path map; no implicit framework
redirection. It refuses longer replacements and does not grow the header. Import
ordinals, fixups and executable instructions are unchanged. All modified signatures
are stale. This command alone cannot create a runnable iPad app.

The legacy `bash tools/build_probe.sh` is an internal UIKit compilation check.
Its output is not Excel and must not be published as a release.
No provisioning profile, developer identity or private credentials are included.
This build cannot be compiled in the present Linux environment without an Apple SDK/toolchain.

.github/workflows/probe.yml runs tests and builds that probe on a macOS runner.
.github/workflows/analyze.yml downloads two pinned official Microsoft packages, checks
the installer certificate, extracts without installation and uploads ONLY reports.
Microsoft binary payloads are never committed or uploaded as CI artifacts.

The user created public repository aaULTra/iOSExcel. Source and derived metadata reports
have been committed through the connected GitHub tools. No Microsoft package or binary
is committed. The probe workflow runs on push. Analysis can also be triggered by the
analysis pull-request event. CI execution status is recorded separately as results arrive.
The Microsoft-containing build pipeline remains gated on the compatibility and
licensing findings; it is not replaced with a misleading nonfunctional Excel IPA.

A main-only experiment (does not create an app):
```
python3 tools/excel_retarget.py 'private/extracted/Microsoft Excel.app/Contents/MacOS/Microsoft Excel' private/Excel-arm64-ios --log private/main-retarget.json
```

The analysis workflow also runs dependency_map.py and audit_sdk.py against the runner's
actual iPhoneOS SDK. The latter needs PyYAML (pinned in CI), reads .tbd declarations
and reexports, and reports unknown schemas/unresolved reexports explicitly. A declared
symbol is NOT evidence of ABI/behavioral compatibility; an unresolved export is not
proof the device lacks a symbol. The first iPhoneOS 18.5 SDK audit completed successfully; results are in docs/evidence/ios-sdk-audit-16.55.json.

Large derived inventories/graphs in source are gzip-compressed (*.json.gz); decompress
them before passing to tools expecting JSON. Generated CI reports remain ordinary JSON.

Successful runs: probe 38816769202 and 38816839581; official-package analysis
38816989758. The first analysis run stopped on an overly specific pkgutil output-string
check; it was fixed to use pkgutil plus spctl installer assessment and explicit Microsoft
signer verification. Both 16.53 and 16.55 jobs then succeeded.

The compatibility workflow compiles the startup shim with warnings treated as errors,
runs native Foundation contracts, compiles/signs the iOS arm64 dylib, verifies exact
exports, and then downloads/verifies the official package. It checks the actual main
nib with test stand-ins and captures runtime AppKit type metadata without loading Office.
It uploads reports only. Successful startup runs are 38820211943 and 38820609645 (latest activity/method inspection changes).
`tools/objc_startup.py` independently inspects selected real class/method metadata;
`tools/shim_coverage.py` compares the current dylib names with the actual startup imports.
Neither tool claims a working implementation merely because a name is exported.

## Actual startup binary preparation (not an app)

```
python3 tools/loader_plan.py 'private/extracted/Microsoft Excel.app' --inventory docs/evidence/excel-16.55.json.gz --graph docs/evidence/dependencies-16.55.json.gz --report private/loader-plan.json --output-binaries private/retargeted-images
```

Unlike processing every optional/helper binary in the bundle, this selects the measured
startup closure and verifies each source hash before output. It stages 55 thin arm64
binaries with platform metadata and distinct AppKit/Cocoa imports. No resources, complete
app, provisioning or IPA is synthesized. The untouched original bundle remains the
source of resources for later integration. Full-directory retargeting still rejects
Intel-only inputs rather than guessing which components can be discarded.

The compatibility workflow also runs `tools/test_loader.py` (native dyld binding with
our own C code), stages the real closure, and calls `tools/build_facades.py` to build
and verify iOS forwarding dylibs against the actual compiled shim. Only reports are
uploaded. Numeric facade versions meet the measured load requirements; missing API
implementations remain missing.

## Screen contracts

`bash tools/test_screen.sh` builds native geometry/failure tests and compares nine method
encodings against captured arm64 AppKit metadata. The compatibility workflow runs this
before downloading Microsoft resources and includes ExcelScreen.m in the signed iOS
shim. `tools/test_screen_simulator.py` separately builds an internal simulator-only app,
creates an isolated available iPad simulator, and runs the production entry bridge with
synthetic desktop classes/nib. It uploads JSON/log reports, never an app or IPA. Microsoft
binaries and account interaction are absent from that test. The script removes its own
simulator after completing or failing; it does not touch a physical iPad.

## View contracts

`bash tools/test_view.sh` compiles native model tests and checks 32 method encodings
against captured arm64 AppKit metadata. The full compatibility workflow now includes
ExcelView.m in the signed iOS shim and runs these contracts. The internal simulator
host additionally checks NSView/UIView hierarchy agreement, flipped/scaled placement,
actual CoreGraphics drawing callbacks and four positive/negative pixel samples. Its
snapshot is sampled internally; only JSON/log reports are uploaded. No Excel code or
unfinished app/IPA is supplied by these tests.

## Real executable loader experiment

The `real-loader.yml` workflow privately acquires verified Excel 16.55, stages its
55-image startup closure for iOS Simulator (platform 7), compiles the matching shim
and facades, re-signs the copies and attempts the original executable through
`simctl spawn`. Run `tools/run_excel_loader.py` only on a Mac with an installed iPad
Simulator runtime; its official-installer input must already be extracted.
`--system-path-map tools/loader_system_paths.json` applies only recorded,
evidence-backed path fixes and probes their actual runtime counterpart first.

Reports include real dyld stdout/stderr, per-field transformation records, runtime
probe results and a status JSON. Only reports are uploaded. This is not an installed
application or device build and no IPA is created. See REAL_LOADER.md for observed
failures and what this experiment can establish.

## Swift overlay drawing checkpoint

The Swift overlay remains an isolated experiment and is not redirected into Office.
`swift-drawing-contracts.yml` captures genuine Mac pixels, then runs
`python3 tools/capture_swift_appkit.py` and
`python3 tools/test_swift_overlay_drawing.py`. The latter requires exact agreement
for all 96 pixel/state records on a Mac test-context backend and a native iOS
Simulator caller using UIGraphicsPushContext/UIGraphicsGetCurrentContext. Failure
keeps the captured outputs for inspection. The test does not launch Excel or create
an IPA. The Mac-only context setter is compiled only with the explicit test macro;
the iOS implementation uses UIKit's current context.
