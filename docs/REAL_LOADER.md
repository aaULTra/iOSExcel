# Real executable loader investigation

`tools/run_excel_loader.py` is an internal dynamic-loader experiment using the
original Excel 16.55 executable and all 54 Microsoft dylibs in its measured
startup closure. It is not the synthetic view/screen test and not an IPA build.

The workflow verifies the official package hash, Microsoft installer signer and
notarization, extracts without executing installer scripts, and verifies every
source image against the recorded binary inventory. It stages only plain arm64
slices. Original executable text and link-edit data are unchanged before signing;
the logged changes are platform metadata and the existing AppKit/Cocoa imports.
Ad-hoc signing replaces invalidated signatures on the private diagnostic copies.

The test explicitly uses **iOS Simulator platform 7**, and compiles the shim and
forwarding libraries for that same platform. Existing device retargeting remains
**iOS platform 2**. Simulator binaries must never be passed off as device builds.

The original main is MH_EXECUTE, so it is launched through `simctl spawn`, not
`dlopen`. Its original `@loader_path/../Frameworks` hierarchy is retained. This is
a pre-initialization loader investigation, not an installed application lifecycle
test. A future installed host must separately resolve bundle identity, resource
locations, launch registration and scene lifecycle. No inference about those is
made from a successful spawn or the absence of a dyld error.

The process output and simulator unified log are retained in reports. The JSON
result records return status, timeout and whether a recognizable dyld error was
captured. It never infers successful Microsoft entry, activation or workbook
functionality merely from process creation. Expected loader failures are evidence,
not a successful Excel milestone; infrastructure exceptions still fail the CI job.

Only reports are uploaded. Microsoft binaries, copied resources, signing material
and unfinished apps/IPAs are never artifacts. No activation machinery is patched,
no helper or installer script is launched, and no unknown function gets a generic
stub simply to advance loading.

Next changes must follow the first observed failure. Framework paths can be
normalized only after verifying their actual simulator/device counterpart. Missing
framework APIs need typed implementation or a separately justified optional path;
an empty library does not establish compatibility.

## First observed failure

Run 38984254220, source 5802800806c2faf496dc9f572bf18f4e9e16dd05,
on iPad Pro 11-inch (M4) Simulator runtime 26.2: dyld reported the real main
and 33 Microsoft dylibs mapped, then aborted (return code 134) on
`/System/Library/Frameworks/Security.framework/Versions/A/Security`.
The runtime explicitly reported no file/cache image at that versioned path.
The Microsoft entry point was not reached. Reports are retained under
`docs/evidence/real-loader-first-*`. The green workflow denotes successful
evidence collection, not successful Excel startup.

The next experiment rewrites that one library identity across the closure to
`/System/Library/Frameworks/Security.framework/Security`. Before attempting Excel,
a separately compiled Simulator process must successfully dlopen that exact path
and resolve SecItemCopyMatching from it. This validates path loading only, not all
Excel's Security imports or licensing behavior.
