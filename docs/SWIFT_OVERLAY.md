# AppKit Swift overlay boundary

Actual loader 39023211961 (90de734c9ed10ca9075dd5581e8ad9fa78b3d43e)
passes ServiceManagement and stops before Microsoft entry at
/usr/lib/swift/libswiftAppKit.dylib, referenced by FluentUI. The same overlay is
loaded by CocoaUI, mso40ui and mso99. All 55 Microsoft and eight owned images map;
exit 134, no timeout, no Excel initialization or activation.

The exact three imported names are:

- _$s10Foundation9IndexPathV6AppKitE4itemSivg
- _$sSo6CGRectV6AppKitE4fill5usingySo22NSCompositingOperationV_tF
- __swift_FORCE_LOAD_$_swiftAppKit

Native capture 39023810431 used Apple Swift 6.1.2, MacOSX15.5 SDK and arm64 Mac
compiler probes. SIL references match both imported function names exactly:

- IndexPath.item getter: @convention(method) (@in_guaranteed IndexPath) -> Int.
- CGRect.fill(using:): @convention(method) (NSCompositingOperation, CGRect) -> ().

The measured native IndexPath size/stride/alignment is 17/24/8 bytes; CGRect is
32/32/8 and NSCompositingOperation is 8/8/8. Size alone does not prove cross-platform
representation or compatibility with the older Office compiler. A C function with
an ad-hoc symbol alias does not establish the required Swift calling convention.

Five valid two-component IndexPaths return their second component, including
Int.max. Invalid and non-two-component cases remain unmeasured. The exact Mac SDK
enum declaration yielded 29 compositing values (0 through 28, with their actual
names recorded); its raw type is NSUInteger/unsigned long. No drawing was executed.
The force-load name has no function reference in the captured SIL and its data
contract remains unmeasured. Its role is not inferred to be a callable API.

Evidence: docs/evidence/swift-appkit-contracts.json and swift-appkit-values.json.
These contain metadata and own-probe results, not an Apple implementation.

Next implementation gates are compiler-generated matching Swift exports, actual
iOS type/ABI and cross-call validation, native drawing/state contracts for supported
compositing, and the force-load data contract. Unsupported drawing must fail
visibly. No overlay redirection or weakened load has been applied. A successful
capture is not a repaired loader, Excel startup, rendering or workbook milestone.

Reproduction is automated by .github/workflows/swift-appkit-contracts.yml using
original probes in tools; it does not download or execute Microsoft code.
