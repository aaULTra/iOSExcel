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

On macOS with Xcode: `bash tools/build_probe.sh` creates a standalone ad-hoc signed
UIKit probe IPA for re-signing by the user's sideloading tool. It is NOT Excel.
No provisioning profile, developer identity or private credentials are included.
This build cannot be compiled in the present Linux environment without an Apple SDK/toolchain.

.github/workflows/probe.yml runs tests and builds that probe on a macOS runner.
.github/workflows/analyze.yml downloads two pinned official Microsoft packages, checks
the installer certificate, extracts without installation and uploads ONLY reports.
Microsoft binary payloads are never committed or uploaded as CI artifacts.

The user created public repository aaULTra/iOSExcel. Source and derived metadata reports
are being committed through the connected GitHub tools. No Microsoft package or binary
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
proof the device lacks a symbol. No SDK audit result has been produced yet.

Large derived inventories/graphs in source are gzip-compressed (*.json.gz); decompress
them before passing to tools expecting JSON. Generated CI reports remain ordinary JSON.
