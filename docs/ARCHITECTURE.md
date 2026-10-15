# Architecture and feasibility gates

Current implementation: Linux-compatible installer extraction, recursive static Mach-O
inventory, conservative copied-tree metadata retargeting, and source for an isolated
UIKit diagnostics probe. No Excel execution path is implemented.

## Intended runtime (conditional, unproven)

A signed iOS main executable must start UIApplicationMain normally. A scene owns the
UIKit window. ExcelShim would implement the ABI and semantics of the desktop APIs
actually used by Excel and its Microsoft frameworks. A validated entry bridge would
then invoke Excel on the main thread while keeping UIKit responsive.

We have NOT assumed that dlopen accepts Excel's MH_EXECUTE image, that changing its
filetype makes it a valid dylib, that its main can run on a worker, or that calling it
again is safe. Initializers, ObjC class registration, two-level binding ordinals,
resource bundle identity, exit behavior and AppKit run-loop ownership all need evidence.
A pure UIKit probe is separate so it cannot be mistaken for a desktop Excel startup.

## Packaging plan, not an implemented Excel bundle

Payload/ExcelPort.app would contain an iOS bootstrap executable, Frameworks with
re-signed iOS-targeted dependencies and libExcelShim.dylib, original Excel resources
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
