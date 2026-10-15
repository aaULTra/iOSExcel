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
