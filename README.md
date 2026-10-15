# ExcelPort research

**Exact status (2026-10-15): real Excel binaries extracted and statically analyzed;
M2 metadata experiment passed; Microsoft Excel has NOT launched on iPadOS.
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
| M1 — dependencies | Static recursive inventories and load graphs complete; iOS SDK symbol audit, dynamic loads and runtime contracts pending |
| M2 — retarget main | Platform metadata changed successfully on real 16.55 main; four bytes differ in the arm64 slice; 41,983,228-byte __text unchanged |
| Relevant embedded metadata | All 55 resolved startup images passed an in-memory platform retarget; paths/resources not yet repackaged |
| M3–M6 — loader/shim/UIKit/Excel initialization | NOT tested for Excel; isolated UIKit probe source prepared, not compiled or run |
| M7–M15 — desktop UI/workbooks | NOT implemented or tested |

## Deliverables

- `docs/COMPATIBILITY.md`: version comparison, dependency map, blockers and feasibility.
- `docs/RESEARCH.md`: official sources, current CyPort findings and activation evidence.
- `docs/ARCHITECTURE.md`: conditional runtime and lifecycle design.
- `docs/BUILDING.md`, `docs/DEBUGGING.md`: reproducibility and first-failure procedure.
- `docs/evidence/`: actual binary metadata, imports, Objective-C strings, original
  entitlements, graph, installer hashes and retarget verification. Metadata only.
- `tools/`: safe extractor, Mach-O reader, dependency mapper, entry probe and retargeter.
- `shim/`, `app/`: **diagnostics-only** shim and standalone UIKit lifecycle probe.
- `.github/workflows/`: prepared tests/probe build and official-package analysis workflows.

`python3 -m unittest discover -s tests -v` runs the synthetic safety/regression tests.
See BUILDING before running a retarget: recursively processing the entire original
bundle deliberately fails on Intel-only files. A main-only experiment is supported.
Do not delete dependencies to force that check to pass.

## Immediate next gate

Run the prepared macOS CI to cross-check inventories with Apple tools, compile the
standalone probe and audit required symbols against the actual iPhoneOS SDK.
The user created https://github.com/aaULTra/iOSExcel. Source is being committed through
the GitHub connection; CI compilation, SDK audit and device milestones remain pending.
Even a successful probe does not establish any Excel startup milestone.
