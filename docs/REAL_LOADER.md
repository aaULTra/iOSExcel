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

The second run, 38984771895 (cd366eba2e33ac41b61d9f459ef733e4af165753),
compiled and signed the path fix, but its standalone canonical Security probe
exceeded the original 60-second process timeout before any result was captured.
Excel was not attempted in that run. This is an infrastructure/probe failure,
not evidence that canonical Security is absent or that Excel advanced. The next
run adds pre-/post-dlopen stderr markers, retains partial timeout output, allows
a bounded 180-second probe and audits the actual required Security symbol names
without invoking them.

## Security path verified; next observed failure

Run 38985243018, source 344e5fd5c1c3f62a8ec993c6002e41a7d2eb42d6,
verified canonical Security loading and SecItemCopyMatching lookup in the same
Simulator. The required-symbol audit found 131 of 183 names and reported 52
missing, including desktop keychain/ACL/transform operations. No API was invoked
and this does not establish device behavior or activation. The cold first probe
took approximately 111 seconds to return; its original 60-second limit was too
short to obtain this result.

The actual Excel attempt then mapped 39 Microsoft images and aborted on
`/System/Library/Frameworks/Accelerate.framework/Versions/A/Accelerate`.
The entry point remains unconfirmed. Reports: `docs/evidence/real-loader-security-*`.

Two real failures now identify one consistent path-format issue. The next script
normalizes versioned Apple framework paths only when an SDK stub exists and a
same-runtime batch probe successfully loads the canonical counterpart. Missing
SDK/runtime counterparts remain unchanged and are reported, not replaced with
empty libraries. All required symbol names are audited without calling them.
This consolidates the same path repair while retaining full two-level import
indices and per-field modification logs. A single probe process avoids paying
the first cold process-launch cost separately for each framework. Every API
reported missing remains unimplemented; normalization is not API compatibility.

## Consistent path normalization passed

Run 38986113826 (9d578f1ce94ee83eaaffef2f9c3504bed749f71f), same M4 iPad
Simulator/runtime: all 35 SDK-matched canonical framework paths loaded in the
batch probe. Runtime lookup found 1,800 of 1,961 queried symbol names; 161 were
missing. This is an export lookup on Simulator only, not a device or behavior
guarantee. 309 path fields were rewritten across the actual hash-verified closure.
The transform remains byte-checked outside logged fields before re-signing.

The real loader again mapped 39 Microsoft images, then aborted (134) on
ApplicationServices.framework. Its canonical counterpart was absent from the
SDK and therefore was not substituted or fabricated. Eleven such absent SDK
counterparts are listed in the transform evidence; absence from this SDK alone
is not a proof of absence from every device runtime.

The first remaining required compatibility library is now ApplicationServices,
with 40 imported names (printing, pasteboard, shape and zoom operations). Their
actual Mac SDK declaration capture is the next implementation gate. No Microsoft
entry/initialization, UIKit lifecycle, activation or workbook milestone is claimed.
Evidence: real-loader-latest.json, real-loader-paths.stderr.log and the compressed
real-loader-path-transform.json.gz.

## ApplicationServices mapped; ExceptionHandling is next

Run 38987517689 at 96ab66967d2dacb358e76321a8d9947cbc284974 mapped
ExcelApplicationServices.dylib and ExcelCocoa.dylib, then aborted on the original
versioned ExceptionHandling path. The facades' dependency shim had not yet been
observed initialized; no Microsoft entry or API execution is claimed. The new
ApplicationServices numeric compatibility requirement was measured as 1.0.0.
Its six redirects brought the base facade path changes to 74.

The original diagnostic counter used a shared Contents prefix and incorrectly
counted the two owned facades as Microsoft images (41). Classification against
the exact recorded vendor closure yields 39 Microsoft images and two owned
facades; the latest report records this correction and preserves the raw report.
The counter now uses exact closure membership.

Before deciding the next missing-framework treatment, SDK-absent canonical paths
are also checked with dlopen_preflight. This checks link compatibility without
loading initializers, does not query exports, and never causes automatic path
substitution. A positive preflight can still require further provenance/ABI
investigation, particularly on Simulator where host-macOS images must not be
mistaken for iPadOS frameworks. Successfully loaded SDK-backed images additionally
record their actual dyld path and Mach-O platform.

ExceptionHandling has zero direct undefined-symbol imports in the measured
Microsoft closure; that alone does not prove its initialization or dynamic lookup
is unnecessary. Apple's reference describes optional Objective-C exception
monitoring via NSExceptionHandler. No exception framework has been removed or
replaced on this evidence yet.
https://developer.apple.com/documentation/exceptionhandling/
https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/dlopen_preflight.3.html

## Guarded optional diagnostics experiment advanced to Kerberos

Run 38989112909 (c54adbd283588a19ac54c222155812c657894a8d) passed the
checked undefined-symbol and classic-bind guards for the unused ExceptionHandling
load. Only its load command kind was weakened; binding indices, executable text
and link-edit data were preserved before signing. The actual loader advanced to
`/System/Library/Frameworks/Kerberos.framework/Versions/A/Kerberos` and aborted
(134) before the Microsoft entry point. 39 Microsoft images and two owned
facades mapped. A green workflow still means failure evidence was captured.

Unlike ExceptionHandling, Kerberos has five measured imports:
`GSS_C_NT_USER_NAME`, `krb5_init_context`, `krb5_free_context`,
`krb5_get_host_realm`, `krb5_free_host_realm`. It cannot pass the optional-load
guard and has not been removed, weakened, redirected or stubbed.
`tools/audit_kerberos.py` compares actual public SDK declarations and probes
these names against SDK-backed GSS in an isolated iPad Simulator process.
It records provider image/platform provenance and never invokes those APIs,
passes credentials or runs Excel. Missing names and macro aliases remain
explicit; finding exports alone would not prove ABI or behavior compatibility.
