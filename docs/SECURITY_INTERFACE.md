# SecurityInterface loader investigation

Actual run 39021819752 (source 50292f932906898b30344c0b501f3ba5d2e98a77)
failed before entry at SecurityInterface.framework, referenced by osfstorage2.
All 55 Microsoft images mapped. The two measured imported classes are
SFCertificateTrustPanel and SFChooseIdentityPanel. This is not a zero-import
framework; the optional-load weakening policy does not apply.

Actual MacOSX15.5 SDK capture in 39022239117 resolved both class declarations,
including 21 methods and their exact types. Evidence:
docs/evidence/security-interface-declarations.json. The global selector inventory
includes sharedCertificateTrustPanel, runModalForTrust:message:,
runModalForIdentities:message: and the identity-sheet selector. This is candidate
information, not attribution of each message send to a particular Office caller.

Apple describes these classes as certificate-trust editing and identity-selection
UI. A return value cannot safely be invented to replace a user's decision:

- https://developer.apple.com/documentation/securityinterface/sfcertificatetrustpanel
- https://developer.apple.com/documentation/securityinterface/sfchooseidentitypanel/runmodal(foridentities:message:)
- https://developer.apple.com/documentation/securityinterface/sfcertificatepanel

The guard in shim/ExcelSecurityInterface.m preserves the expected named class chain
(NSWindow -> NSResponder, NSPanel -> NSWindow, SFCertificatePanel -> NSPanel,
SFCertificateTrustPanel -> SFCertificatePanel, SFChooseIdentityPanel -> NSPanel).
It is a loader diagnostic guard, not a window implementation. All allocation
paths through NSObject's normal alloc/new/allocWithZone: entry points are rejected
with ExcelShimUnimplemented. Three shared-panel factories also log and raise;
unknown selectors fail visibly. No panel object, identity, certificate acceptance,
trust change, authorization, account or activation result is produced. No Security
framework call is made. This explicitly prevents unsupported dialogs from silently
turning into a successful security decision.

The native workflow first reads Apple class metadata without instantiating panels,
then runs the guard in a separate Foundation-only process. It compares five direct
superclasses, three factory method encodings and allocation encodings; it checks
15 ordinary allocation paths and three factories stop. The first native metadata build (39022357419) omitted AppKit for direct NSWindow/NSPanel references; this was corrected. The next build exposed existing unused parameters in the Mac-inactive UIKit entry, so the guard test now uses the existing native contract flags. Native run 39022498941 passed the exact hierarchy/ABI comparison and all rejection checks. The baseline links Apple AppKit/SecurityInterface; the guard process links neither. A sixth distinct forwarding facade is now integrated for the next real loader test; its outcome and UIKit provenance checks are pending. No claim of
Excel initialization, UI, workbook use or legitimate iPadOS activation follows.

The eventual real implementation must use supported platform trust/identity UI and
preserve user decisions and Microsoft authentication. If that is unavailable,
the associated feature must stay unavailable, with its caller handling an actual
failure. A diagnostic exception is deliberately not claimed as that final behavior.
