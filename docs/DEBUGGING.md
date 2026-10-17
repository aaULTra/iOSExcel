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

## AppKit/Cocoa redirection checks

When diagnosing loader bindings, retain the distinct ExcelAppKit.dylib and
ExcelCocoa.dylib identities. Do not merge them into one load command or introduce
flat-namespace lookup to hide missing exports. Both reexport libExcelShim.dylib.
The known-good native binding fixture and full vendor modification plan live under
docs/evidence. A successful fixture run proves only that forwarding topology with our
own code; it is not evidence that any particular Excel import or initializer succeeds.

## Screen adapter

NSScreen logs invalid bounds/scale, conversion overflow, detached scenes and background
thread access before raising a predictable exception. It returns no screen before a
UIKit scene is attached. deviceDescription deliberately omits physical DPI and display
ID with a log message; investigate the real caller if it requires those missing values.
The internal simulator result is written to Documents/screen-simulator-result.json;
the workflow uploads it as a report, plus process/shim logs on failure. These logs prove
only the adapter/bridge behavior with synthetic desktop code, not any Excel milestone.

## View projection

NSView logs cycles, invalid/overflowing geometry, unrelated roots and unfinished
window-coordinate conversions before raising. Its UIKit projection preserves the
legacy selected target's clipping default and adapts drawRect: coordinates explicitly.
The view_contracts object in the internal simulator report records actual draw callback
counts and pixel assertions. Passing those synthetic checks is not an Excel UI run.
The native model report checks hierarchy lifetime and 32 exact method encodings.

## Actual Excel loader

Use `real-loader-result.json` and `real-loader.stderr.log` from the real-loader
workflow, not the synthetic screen/view result, to identify the first actual dyld
failure. A `DYLD_PRINT_LIBRARIES` mapping line does not prove that an initializer or
the main entry ran. A green evidence-collection workflow does not mean Excel started.
Simulator platform 7 must not be confused with device platform 2.

Standalone system-library probes print PROBE_START before dlopen and
PROBE_DLOPEN_OK afterward. A timeout with no start marker differs from a started
probe stuck loading a library. Retain partial output and the infrastructure exception;
do not label either as an Excel failure if its executable was never attempted.
Runtime symbol audits use dlsym without invoking functions: a found name proves
lookup only, not argument layouts, semantics or legitimate activation.

## Cold simulator module compilation is a build failure

SDK audit run 39020471590 timed out while clang built the standalone Simulator
Objective-C helper with a 60-second compile limit; no API result or Excel regression
was established. The audit now builds that helper before Simulator boot and permits
a bounded 180 seconds for this cold compilation. Runtime calls retain their own
time limits. Actual Excel runs independently repeated the provider gate successfully.

The next standalone audit (39021497623) passed that compilation but hit its
separate 60-second CoreSimulator device-enumeration limit. The device-list
timeout is now 120 seconds, matching the already-tested real loader harness.
This was before any Simulator API call or Microsoft process in that audit.
