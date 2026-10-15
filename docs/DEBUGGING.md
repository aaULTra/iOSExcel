# Runtime evidence and first-failure procedure

No device runtime has been observed. No Excel launch or workbook milestone is claimed.

The standalone probe links libExcelShim.dylib at normal launch, starts UIApplicationMain,
creates a UIWindowScene window and writes lifecycle/heartbeat messages to
Documents/excelshim.log. Info.plist enables Files sharing. It neither loads nor
bundles Excel and cannot establish Excel M3–M6. No special memory entitlements requested.

For each physical-device run retain: exact source commit, artifact hash, signing tool,
iPadOS build, install result, crash .ips (if any), console/dyld output, and excelshim.log.
A dyld failure before main may produce no app log; system crash evidence is required.
An uncaught Objective-C exception is logged. Signals, jetsam and forced termination
still require the OS diagnostic report; the shim does not promise to catch them.

Resolve the FIRST meaningful failure only: installation/signature -> dyld/platform ->
missing library/symbol -> Objective-C registration -> startup -> window/drawing ->
input -> document I/O. Rebuild and compare. Do not silence activation failures.

Do not invent Objective-C signatures for missing selectors. A generic integer return
is incompatible with struct/floating-point returns and can silently corrupt state.
Implement known signatures and semantics, log, and raise on unknown behavior.

A future workbook validation must include an untouched fixture, edits of strings and
numbers, cross-sheet formula recalculation, save, reopen in desktop Excel, and comparison
of expected cell values, formulas, styles and archive integrity. A visible grid is not M13.
