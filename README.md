# ExcelPort research

**Exact status (2026-10-17): real Excel binaries extracted and statically analyzed;
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
| M3–M6 — loader/shim/UIKit/Excel initialization | NOT reached for Excel; production UIKit bridge tested with synthetic desktop classes/nib on iPad Simulator; no physical-device run |
| M7–M15 — desktop UI/workbooks | NOT implemented or tested |

## Deliverables

- `docs/COMPATIBILITY.md`: version comparison, dependency map, blockers and feasibility.
- `docs/RESEARCH.md`: official sources, current CyPort findings and activation evidence.
- `docs/ARCHITECTURE.md`: conditional runtime and lifecycle design.
- `docs/LOADER.md`: distinct forwarding dylibs, native two-level binding proof and exact limits.
- `docs/SCREEN.md`: partial scene-backed NSScreen geometry and its validation boundary.
- `docs/VIEW.md`: typed NSView hierarchy, drawing bridge, pixel tests and explicit limits.
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

The current priority is an internal **real Excel executable loader attempt**, using
the original Microsoft startup closure on iPad Simulator. This is separate from
the synthetic UI tests below. See docs/REAL_LOADER.md for the exact method and
limits. The first attempt mapped the real main and 33 Microsoft dylibs, then
dyld aborted on the macOS-versioned Security.framework path. Its entry point
was not reached; no successful Excel initialization is established.

Source: https://github.com/aaULTra/iOSExcel

All 31 Python tests pass. Native startup/nib/delegate contracts, two-level dyld binding,
actual 55-image retargeting, iOS forwarding-library builds and signature checks pass.
The original XLMainMenu archive is checked with explicit test stand-ins, without loading
Excel. Nine NSScreen and 32 NSView method encodings match captured arm64 AppKit contracts.
The partial NSView model preserves NSResponder inheritance, hierarchy ownership and
flipped/scaled coordinates, with a separate UIView projection and typed drawing bridge.

The production UIKit entry bridge and scene/view adapters also passed an
internal iPad Pro 11-inch (M4) Simulator run on 26.2. It exercised a real key window,
UIKit safe areas, scene scale, window-bounds changes and synthetic view drawing. Four
pixel samples verify flipped/unflipped draw placement; hierarchy, scaled coordinates,
visibility, z-order and removal checks pass. The host uses synthetic desktop classes/nib
and contains no Microsoft code. It is not physical-iPad or Excel UI validation.
See docs/SCREEN.md and docs/VIEW.md for exact scope and unsupported behavior.

Current exact export coverage is 16/538 required AppKit names and 6/143 imported classes.
These include partial implementations; exported names are not working API guarantees.
Remaining class/API behavior, framework/resource integration, real Excel UI/text/document rendering
and legitimate activation still block real Excel loader and workbook milestones.

Native view/screen/startup/loader checks: https://github.com/aaULTra/iOSExcel/actions/runs/38982725023

UIKit bridge/screen/view simulator check: https://github.com/aaULTra/iOSExcel/actions/runs/38982725046

Official package/SDK analysis: https://github.com/aaULTra/iOSExcel/actions/runs/38816989758

The first iPhoneOS 18.5 SDK declaration audit found 3,432 required names in parsed
exports and 847 not found there. Some private reexports/absent stubs remain unresolved;
these counts do not prove device availability or absence. No actual Excel milestone
beyond M2 has been reached and no working Excel IPA exists.

Release policy: publish no diagnostic/unfinished IPAs. A working Excel release requires
verified real desktop Excel opening, editing, calculating and saving ordinary .xlsx files.
No Microsoft binary payload, activation data or signing credentials are in this repository.
