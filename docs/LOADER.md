# AppKit/Cocoa loader redirection checkpoint

The selected startup closure has 55 images: one MH_EXECUTE and 54 MH_DYLIB files.
Twenty-four images, including Excel main, directly load both AppKit and Cocoa.
Redirecting both load commands to the same shim would create duplicate dylib paths
and require a separate investigation of ordinal remapping. The retargeter refuses it.

The implemented alternative preserves the original command count, order and load kinds:

| Original dependency | New distinct dependency | Reexports |
| --- | --- | --- |
| AppKit.framework/Versions/C/AppKit | @rpath/ExcelAppKit.dylib | @rpath/libExcelShim.dylib |
| Cocoa.framework/Versions/A/Cocoa | @rpath/ExcelCocoa.dylib | @rpath/libExcelShim.dylib |

Each forwarding dylib has its own identity and an LC_REEXPORT_DYLIB pointing to the
shared shim. This implements no additional desktop APIs. In this build no undefined
symbols were attributed directly to Cocoa, but its explicit load must still resolve.
The numeric compatibility requirements measured across the real closure are AppKit
45.0.0 and Cocoa 1.0.0. The forwarding libraries satisfy those numeric loader checks;
the numbers do not establish behavioral compatibility with either Apple framework.

## What is verified

- Real installer identity, hash and notarization assessed on the Mac runner.
- All 55 source binaries matched their full-file hashes in the recorded inventory.
- Sixty-eight AppKit/Cocoa path fields changed across the closure. Platform metadata
  was retargeted to iOS 18.0. Command order, original library indices and load kinds remain.
- Every output byte outside the logged platform/path fields matches the original
  arm64 slice. Per-image executable __text and complete __LINKEDIT hashes also match.
- A fresh 219 MiB binary-only staging tree was written locally, without modifying
  the original Excel bundle. The same operation passed on a Mac runner.
- A native two-level binding fixture first ran against two original libraries, then
  ran with those libraries removed and the same two import ordinals resolving through
  separate facades into one shared implementation. Only our own C code executes.
- Actual iOS arm64 forwarding libraries compiled, reexport identity/platform/version
  checks passed, and ad-hoc signature verification passed.
- Linux and Mac generated identical loader plans for the actual Excel binaries.

The closure report, native binding contract and iOS facade metadata are retained in
`docs/evidence/loader-plan-16.55.json`, `native-loader-contract.json` and `ios-facades.json`.
No Microsoft binary payload is committed or uploaded as a CI artifact.

## What this does not establish

This is an M2 binary preparation checkpoint, not M3. Excel has not completed loading or reached its entry point. A subsequent real
Simulator loader attempt mapped Microsoft images and captured its first failure;
see REAL_LOADER.md.
The current shim still exports only 16/538 required AppKit names and 6/143 classes.
The remaining framework paths and symbols, class behavior, initializers, resource
identity, UI, text, document access and legitimate activation remain unresolved.
The original framework hierarchy/rpaths are retained in the binary-only experiment.
A future iOS bundle layout must explicitly validate its own resource and rpath rules.
Original code signatures are stale after patching and all vendor images need legitimate
app re-signing before a device loader test. No app bundle or IPA is produced by this tool.

Sources for the forwarding approach and two-level/version semantics:
https://github.com/apple-oss-distributions/ld64/blob/main/doc/man/man1/ld-classic.1
https://github.com/apple-oss-distributions/ruby/blob/main/reexport.sh

## ApplicationServices extension verified at the loader boundary

The actual loader subsequently stopped on ApplicationServices. The redirection map
now has a third distinct facade, ExcelApplicationServices.dylib, backed by the
measured typed partial C layer. This adds six framework path rewrites to the
original 68 AppKit/Cocoa changes. The historical native fixture remains a proof of
the original two-facade topology. Real-image facade version/signature checks passed, and its load was observed in
38987517689; native Apple geometry and C ABI tests passed in 38988363451.
This establishes partial API contracts and loader identity, not printing, clipboard
or Excel initialization; see APPLICATION_SERVICES.md.

## Fourth facade: genuine Kerberos forwarding

ExcelKerberos.dylib adds the one strong Kerberos load to the explicit map, retaining
its original two-level index. It forwards to the shared shim, whose four wrappers
call actual Apple functions and whose legacy OID data object references the genuine
GSS descriptor. Native and M4 Simulator 26.2 contracts passed before integration.
The private-provider dependency and actual runtime gate are described in KERBEROS.md;
the real loader passed this dependency in 39019181596 and stopped at NetFS. This is not a zero-import optional
load and does not use the ExceptionHandling policy.

## Fifth and sixth forwarding identities

ExcelScriptingBridge.dylib preserves the real SBApplication import and forwards to the explicitly unavailable automation layer. Actual loader 39021819752 passed this dependency, mapping all 55 Microsoft images and six owned images before failing at SecurityInterface. Device-target preparation 39021819832 verified 77 path changes and five facade identities.

ExcelSecurityInterface.dylib is a sixth forwarding identity for the actual two imported certificate/identity panel classes. Native metadata/guard run 39022498941 passed five superclass relationships, factory/allocation ABI encodings and explicit rejection of panel creation. Actual loader 39022585600 passed the SecurityInterface load boundary and stopped at ServiceManagement. UIKit run 39022585578 passed class image provenance and all rejection checks; this is a fail-closed diagnostic gate, not security UI or a usable desktop window implementation.
