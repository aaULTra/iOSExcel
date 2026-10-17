# Architecture and feasibility gates

Current implementation: installer extraction, recursive static Mach-O inventory,
hash-verified startup-closure retargeting with distinct AppKit/Cocoa/ApplicationServices/Kerberos/ScriptingBridge/SecurityInterface forwarding dylibs,
an observed-format startup nib decoder,
limited AppKit startup classes and a UIKit entry bridge. Native contract tests and
arm64 iOS compilation/signature checks pass. Real Microsoft images have been passed
to Simulator dyld; Microsoft entry and application initialization remain unreached.

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

## Preserving dependency identities

AppKit and Cocoa are redirected to distinct forwarding dylibs rather than collapsing
their load commands into one dependency. Both reexport the same shim, preserving the
existing two-level library indices and leaving binding payloads unchanged. The native
loader fixture verifies this topology with original C code. See LOADER.md for exact
measurements and the explicit boundary between loader plumbing and API compatibility.

## Scene workspace geometry

The scene entry bridge attaches NSScreen to its actual UIWindow before desktop nib
initialization. Screen coordinates expose that application workspace with a bottom-left
origin; UIKit safe areas and point-to-backing scale are adapted explicitly. No physical
DPI or CG display identifier is invented. Native method encodings match captured AppKit
contracts. This partial class adds no NSWindow/NSView/text/document rendering support.
See SCREEN.md for the test boundaries and unsupported screen functionality.

## Typed view projection

The partial NSView layer keeps NSResponder inheritance and its own model hierarchy;
UIView is a projection rather than a class alias. Strong child ownership and weak
parent/responder references avoid cycles. Frame/bounds transformations account for
mixed coordinate origins and scaling. UIKit dispatches typed drawRect: calls with an
adapted CoreGraphics context; opposite origins are verified with pixel samples.
No compatibility NSWindow is associated yet. Window conversion, constraints, view
archives, input routing and full AppKit rendering remain separate unresolved layers.
See VIEW.md for the implementation and proof boundary.

## Real pre-entry loader gate

The current dynamic experiment runs the original Excel MH_EXECUTE with its original
framework-relative hierarchy using simctl spawn. It does not dlopen an executable or
alter Excel's entry code. Simulator metadata, shim and facades are all explicitly
platform 7; the device retarget remains platform 2. This is deliberately a pre-entry
diagnostic gate, separate from registering an installed UIKit application and its
resource/scene lifecycle. See REAL_LOADER.md for actual observed failures. Only
an explicit entry marker or stronger execution evidence may advance the startup
milestone; mapped-image traces alone cannot.

## Genuine Kerberos forwarding experiment

The legacy Kerberos facade is separate from canonical GSS and preserves its original
import ordinal. Four simple pointer/integer C signatures were compiled against the
actual Mac declarations. The adapter resolves Apple's real implementations through
GSS, validates a common system image and current platform, and retains its library
handle for the lifetime of native contexts. It exports the legacy OID pointer using
the genuine public GSS descriptor. No context, realm, identity, permission or
authentication result is fabricated. Missing providers produce explicit errors.

Native and M4 iPad Simulator 26.2 ownership/data contracts passed in 39018956591.
These functions are supplied by private Heimdal implementation details, so this
remains version-sensitive experimental compatibility. The real loader driver repeats
those tests on its exact runtime before launching Microsoft code. Domain SSO,
Microsoft login and legitimate activation remain unverified. See KERBEROS.md.

## Automation and security boundaries

The ScriptingBridge adapter implements the measured SBApplication -> SBObject hierarchy, but returns nil from all three supported target factories and both constructors. It sends no Apple events and creates no running-app identity. Native method/hierarchy contracts and real UIKit integration passed. Actual loader run 39021819752 passed the dependency; this says nothing about Office message-send behavior.

The SecurityInterface diagnostic preserves five measured class relationships through NSWindow/NSPanel. NSWindow allocation and all shared security-panel factories always log and raise ExcelShimUnimplemented. There is no compatible desktop window instance or trust/identity UI. No security result is substituted. Native guards passed before integration. The separate UIKit test verifies class image provenance and rejection behavior inside a real UIKit host. See SECURITY_INTERFACE.md for actual run evidence and limits.
