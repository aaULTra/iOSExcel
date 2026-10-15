# ExcelPort research

**Exact status (2026-10-16): real Excel binaries extracted and statically analyzed;
M2 startup-image retargeting/redirection checks passed; Microsoft Excel has NOT launched on iPadOS.
No runnable Excel IPA exists.**

Target: Microsoft Excel for Mac **16.55 (21111400)**, official Universal installer.
Compared actual 16.53, 16.55 and 16.113.4 binaries. CyPort main was inspected first at
15b177ff16c2efc76639e1b7479a8fe7ce535f20.

**Assessment:** a usable M13 desktop Excel port is **not practical as a thin CyPort-style
shim** on the evidence so far. Open-ended research could continue with major AppKit,
text/UI, lifecycle and legitimate-activation work. This is not a proof of impossibility
and no initial crash was used as a reason to stop. No device execution has occurred.

The selected startup closure contains 55 bundled arm64 images, 538 distinct AppKit
imports and 143 imported AppKit classes. The main executable has 285 ObjC classes,
74 linked libraries and a direct entry tail-branch to NSApplicationMain. There are
401 nib files in the bundle. UI compatibility is not just NSWindow -> UIWindow.

The attached Office LTSC 2021 package is a **license serializer, not Excel**. It contains
a privileged Mac helper and does not provide an established iPadOS activation path.
Original Excel entitlements reference Microsoft's app groups, identity keychain group
and licensing helper port. No licensing, DRM, device-identity or account bypass exists
in this project. No Microsoft binaries, installers, activation data or signing keys
are included in this repository/archive.

| Milestone | Evidence-based status |
| --- | --- |
| M0 — extracted, native arm64 confirmed | Complete for all three compared versions |
| M1 — dependencies | Static inventories, load graphs and first iPhoneOS SDK declaration audit complete; dynamic/runtime contracts pending |
| M2 — retarget main | Platform metadata changed successfully on real 16.55 main; four bytes differ in the arm64 slice; 41,983,228-byte __text unchanged |
| Relevant embedded binaries | All 55 startup images hash-verified and staged with iOS metadata plus 68 AppKit/Cocoa path changes; code and link-edit bytes unchanged; not an app |
| M3–M6 — loader/shim/UIKit/Excel initialization | NOT tested for Excel; isolated UIKit probe compiled successfully on macOS CI; no device run |
| M7–M15 — desktop UI/workbooks | NOT implemented or tested |

## Deliverables

- `docs/COMPATIBILITY.md`: version comparison, dependency map, blockers and feasibility.
- `docs/RESEARCH.md`: official sources, current CyPort findings and activation evidence.
- `docs/ARCHITECTURE.md`: conditional runtime and lifecycle design.
- `docs/LOADER.md`: distinct forwarding dylibs, native two-level binding proof and exact limits.
- `docs/BUILDING.md`, `docs/DEBUGGING.md`: reproducibility and first-failure procedure.
- `docs/evidence/`: actual binary metadata, imports, Objective-C strings, original
  entitlements, graph, installer hashes and retarget verification. Metadata only.
- `tools/`: safe extractor, Mach-O reader, dependency mapper, entry probe and retargeter.
- `shim/`: incremental desktop startup/nib compatibility code, tested in native contract CI; `app/`: legacy internal UIKit probe.
- `.github/workflows/`: prepared tests/probe build and official-package analysis workflows.

`python3 -m unittest discover -s tests -v` runs the synthetic safety/regression tests.
See BUILDING before running a retarget: recursively processing the entire original
bundle deliberately fails on Intel-only files. A main-only experiment is supported.
Do not delete dependencies to force that check to pass.

## Current CI and next gate

Source is committed at https://github.com/aaULTra/iOSExcel.
Both the UIKit probe build and official-package analysis workflows have succeeded.
The probe and libExcelShim.dylib are arm64 iOS 18.0 binaries built with SDK 18.5;
Apple codesign verification passed. This does not prove installation or device launch.

The macOS analysis verified the Microsoft installer with pkgutil and Apple's installer
assessment, reproduced the inventory and ran a first iPhoneOS 18.5 .tbd audit. It found
3,432 required names in parsed exports and 847 not found there; some libraries have
unresolved private reexports/absent stubs, so these counts are NOT device absence proofs.
No actual Excel loader/UI/activation/workbook milestone beyond M2 has been reached.

Current work implements the observed startup nib, application/delegate wiring and UIKit
entry bridge; see docs/STARTUP.md. Native bounds, nib wiring, delegate callback and
iOS compile/signature checks now pass, including the actual XLMainMenu archive with
explicit test stand-ins. Excel itself was not loaded. The current export report shows
12/538 required AppKit names and 4/143 required classes present; this is name coverage,
not working behavior. Remaining class/API contracts, drawing/text, resource lookup and
legitimate activation still block an Excel loader or workbook milestone.

Probe build: https://github.com/aaULTra/iOSExcel/actions/runs/38816769202

Analysis: https://github.com/aaULTra/iOSExcel/actions/runs/38816989758

No proprietary application binary or activation payload is in this repository.

Release policy: publish no further diagnostic/unfinished IPAs. A working Excel release
requires verified real desktop Excel opening, editing, calculating and saving .xlsx files.

Latest loader validation: https://github.com/aaULTra/iOSExcel/actions/runs/38823800651

All 30 Python tests pass. Native dyld binding, actual 55-image staging, iOS forwarding
library builds and original startup contracts passed. No Excel loader/device milestone
is claimed by those checks.
