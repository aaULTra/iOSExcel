# Incremental desktop startup implementation

The measured Excel entry tail-branches to NSApplicationMain. Its initial XLMainMenu.nib
is NIBArchive v1/coder9, not an NSKeyedArchiver plist. It contains 33 archive objects,
ten archive classes and one outlet connection: application.delegate -> XLAppDelegate.
It instantiates XLDocumentController and NSFontManager but has no visible windows.
This is the first concrete startup contract being implemented, not a workbook UI.

The new compatibility components implement:

- Bounds-checked NIBArchive parsing in Python (inspection) and Objective-C (runtime).
- The observed Foundation collections, custom-object placeholders, existing owner,
  delegate outlet and awakeFromNib ordering. Unknown class/encoding paths fail explicitly.
- NSResponder basics, NSApplication singleton and launch notification dispatch,
  NSFontManager singleton, NSDocumentController singleton/document registration.
- NSApplicationMain -> UIApplicationMain -> foreground -> original desktop principal
  class/main nib/delegate callbacks. The original executable's main is not re-entered.

UIKit owns the event loop. The bridge expects the unmodified resource subtree at
Desktop/Microsoft Excel.app/Contents within a future signed iOS bundle. No such runnable
Excel bundle exists yet. Other imports, class ABI contracts, UI/text/drawing, resource
lookup across frameworks, activation and file I/O remain unresolved.

The native tests use explicit TEST stand-ins for application/delegate/controller classes
when checking the actual Excel nib. This validates the decoder and wiring only. It does
not execute Microsoft code, establish M6, activate Office or render a workbook.
A separate synthetic resource tests launch callbacks using the compatibility classes.
The iOS bridge must compile and export its real symbols, but compilation is not a device run.

References:
https://developer.apple.com/documentation/appkit/nsapplicationmain
https://developer.apple.com/documentation/appkit/nsapplication
https://github.com/matsmattsson/nibsqueeze/blob/master/NibArchive.md
The nib parser is an original implementation of the documented format; no GPL parser
source or Microsoft nib resource is committed.

The compatibility workflow publishes text reports only. Following the user's instruction,
no further diagnostic or unfinished Excel IPA is to be presented as a deliverable.

## Verified checkpoint (2026-10-15)

Run 38820609645 at source 65279df passed native synthetic contracts, the original
Excel startup nib with test stand-ins, foreground/background notification state/order,
real iOS arm64 compilation, ad-hoc signature verification and expected exported symbols.
The original Microsoft installer was independently hash/signature/notarization checked.
Actual startup classes/method type encodings were read statically without loading Office.
Their callbacks include applicationDidResignActive:, which is now wired by the bridge.

The current shim exports 12 of the closure's 538 AppKit names and 4 of its 143 imported
AppKit classes. This is name coverage, not 12 working API implementations. The complete
missing list and runtime AppKit class metadata are retained in docs/evidence. No loader,
Excel initialization, workbook rendering, activation or document milestone is claimed.

The native build required an explicit macOS SDK sysroot and explicit argv nullability.
The test launcher handles macOS Bash 3's empty-argument behavior with nounset enabled.
These failures were fixed and the full workflow was rerun to success.
