# Architecture and feasibility gates

Current implementation: installer extraction, recursive static Mach-O inventory,
conservative copied-tree metadata retargeting, an observed-format startup nib decoder,
limited AppKit startup classes and a UIKit entry bridge. Native contract tests and
arm64 iOS compilation/signature checks pass. Actual Excel execution remains untested.

## Intended runtime (conditional, unproven)

The measured original LC_MAIN entry tail-branches directly to NSApplicationMain.
The proposed primary path therefore keeps Excel as MH_EXECUTE, resolves its
NSApplicationMain import to the shim, and starts UIApplicationMain exactly once.
UIKit foreground activation then reads the original desktop Info.plist/main nib,
creates the real XLApplication/XLAppDelegate/XLDocumentController classes and delivers
startup callbacks. This bridge is implemented but has not run with Microsoft code.
There is no re-entry into Excel main and no second competing AppKit event loop.

The tested nib instantiation uses explicit test stand-ins; it does not establish that
Excel's real constructors or delegate callbacks can finish. In particular, all strongly
linked dependencies, initializers and Objective-C superclass references must load
before the entry bridge is reached. The current AppKit shim covers only a small
fraction of those imports. Runtime binding and class behavior are the next barriers.

No assumption is made that dlopen accepts MH_EXECUTE, that changing its filetype creates
a valid dylib, or that moving its main to a worker is safe. Resource bundle identity,
two-level binding ordinals, framework paths, exit behavior, window/text/drawing semantics
and signing remain separate requirements. The legacy isolated UIKit probe remains an
internal compilation check and is not a release artifact.

## Packaging plan, not an implemented Excel bundle

Payload/ExcelPort.app would contain the retargeted Excel main executable using the
UIKit entry bridge, Frameworks with re-signed iOS-targeted dependencies and
libExcelShim.dylib, original Excel resources
in a stable private resource subtree, and an iOS Info.plist. Framework path flattening
must be collision-aware; NSBundle resource lookup and nib loading cannot be fixed by
blindly moving files. Mac helpers/XPC services cannot simply be launched as iOS children.

Mutable workbooks and logs belong in Documents/Application Support. Document pickers
need security-scoped access and explicit coordination; save correctness must precede
any usable-release claim. Preserve original Microsoft binary copies and hashes.

## Licensing gate

The original activation decision and cryptography must remain intact. Native iOS APIs
may be used only where they provide the real required operation; returning fabricated
identity, permissions or entitlement success is outside the design. A normal iOS app
cannot install a privileged Mac launchd helper. It is not yet established whether
Microsoft's subscription path can operate without that helper or which required
Mac-specific identity/keychain functions it uses. The supplied volume serializer does
not solve this. Without a legitimate activation path, M13 is not achievable as specified.

## Why the CyPort analogy is limited

A game can draw its own entire interface into a Metal surface and need only a thin
Cocoa window shell. Excel's native controls, Office UI frameworks, text layout,
AppKit subclass behavior, nib archives, accessibility and document lifecycle can require
substantial AppKit semantics. Optional printing/cloud features may be postponed only
after distinguishing eager-load requirements from optional runtime branches.
