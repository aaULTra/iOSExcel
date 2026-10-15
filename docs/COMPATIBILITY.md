# Compatibility assessment

**Verdict: NOT PRACTICAL as a small CyPort-style port to a usable desktop Excel app.
GO WITH MAJOR WORK only for open-ended compatibility research.** This is an engineering
assessment of measured scope, not a proof that all possible ports are impossible.
No launch crash was used as a reason to stop: Excel has not run here at all.
The declared M13 goal is NOT currently shown achievable with legitimate activation.

## Version selection from actual packages

| Measured property | 16.53 (21091200) | 16.55 (21111400), selected | 16.113.4 (26100421) |
| --- | ---: | ---: | ---: |
| Main minimum macOS | 11.0 | 11.0 | 14.0 |
| Main SDK metadata | 11.3 | 11.3 | 26.4 |
| Main native arm64 bytes | 54,181,072 | 53,770,512 | 97,172,000 |
| Main linked libraries | 74 | 74 | 113 |
| Main undefined symbol records | 6,723 | 6,560 | 11,676 |
| Main ObjC class-list entries | 285 | 285 | 740 |
| Main ObjC protocol-list entries | 85 | 86 | 156 |
| Main ObjC method-name strings | 6,456 | 6,465 | 10,725 |
| All bundled Mach-O files | 211 | 212 | 194 |
| Files with a plain arm64 slice | 183 | 184 | 194 |
| Resolved static startup image closure | 55 | 55 | 51 |
| Distinct AppKit imports in that closure | 538 | 538 | 624 |
| AppKit classes imported by that closure | 143 | 143 | 154 |
| Bundled nib files | 401 | 401 | 344 |

Counts include weak loads in the resolved closure and exclude dynamically loaded images.
All versions have one unresolved WEAK bundled load of MsgrLibClient from mso99; that is
not treated as a required missing dependency. No unresolved strong bundled load was
found by the current static resolver. Foundation/System umbrella re-exports mean that
AppKit-attributed names are a lower bound on desktop UI dependencies, not a complete API census.

16.55 offers a modestly smaller executable/import surface than 16.53 with the same
observed core AppKit burden and macOS baseline. Current Excel has fewer bundled images
but markedly more main-executable imports/classes and AppKit imports. Image count alone
would have selected badly. 16.55 is an experimental target, not a recommended supported
Office version or a demonstrated activation-compatible iPad build.

## Dependency map (16.55)

The full per-image/per-edge graph, import names, load kinds and resolved paths are in
`docs/evidence/dependencies-16.55.json.gz`; the complete inventories are in `excel-*.json.gz`.

| Dependency group | Observed components | Port consequence |
| --- | --- | --- |
| Excel main | Native arm64 MH_EXECUTE; LC_MAIN tail-branches to NSApplicationMain; XLApplication principal class; XLMainMenu nib | Must provide real AppKit startup/class/nib semantics and integrate UIKit lifecycle |
| Shared Microsoft core/UI | mso20, mso30, mso40ui, mso99, CocoaUI, FluentUI, Forms, Gfx, OfficeArt, Chart, SmartArt, WLMKernel, WLMGraphicsDevice, dwrite10, MicrosoftRichEdit | These recursively import desktop UI/text/drawing behavior; retargeting them does not implement it |
| Authentication/licensing | ADAL4, MicrosoftCredui, MicrosoftFBA, MicrosoftIvy, WinCrypto, mbukernel; external licensingV2 helper entitlement | Preserve real activation; privileged helper/device identity/keychain dependencies remain unresolved |
| iOS framework families (symbol compatibility NOT yet audited) | Foundation, CoreFoundation, CoreGraphics, CoreText, CoreImage, ImageIO, QuartzCore, Metal, Accelerate, CFNetwork, Security, WebKit | Check each imported symbol and selector against the selected iPhoneOS SDK/device; flattening paths alone is insufficient |
| Desktop Apple dependencies needing replacement or symbol-level audit | AppKit, Cocoa, ApplicationServices, CoreServices, DiskArbitration, IOKit, OpenGL, SecurityInterface, ScriptingBridge, ServiceManagement; additional direct loads include ExceptionHandling, Kerberos, NetFS and Quartz | AppKit is a confirmed desktop framework. Other mixed/umbrella/private families need exact symbol audits, not blanket redirection |
| Helpers under SharedSupport | Microsoft Error Reporting.app; Microsoft.Mashup.Container.app; language proofing bundles | May be deferrable, but their executable/helper launch and fallback paths need verification |
| XPC/IPC | No .xpc bundles or Contents/XPCServices in these packages; original main entitlements request licensingV2.helper.port lookup | Absence of an embedded XPC bundle does NOT mean no external Mach/XPC dependency |
| Optional initial features | VBA, osf add-ins, cloud/coauthoring, Mashup/Power Query, printing | Some relevant frameworks, including VBA, are strongly linked at startup; cannot just delete them because their feature is deferred |
| Intel-only bundled compatibility files | 28 files in 16.55, mainly old Swift libraries plus libntlm | None resolved into the plain arm64 static closure; never claim all 212 images are ARM64 or blindly retarget them |

MacOS, Frameworks, Resources, SharedSupport and Info.plist were inspected recursively.
Contents/PlugIns, Contents/XPCServices and Contents/Helpers are absent, rather than
silently omitted from analysis. Helpers actually live in SharedSupport.

## Why the boundary is substantial

The selected executable alone imports 181 AppKit symbols. Its resolved Microsoft
startup closure imports 538 distinct AppKit symbols and 143 AppKit classes, including
NSDocument/NSDocumentController, NSNib, NSGraphicsContext, NSTextView, NSLayoutManager,
NSTableView, NSOutlineView, NSCell subclasses, NSScrollView, NSMenu and NSWindow.
CyPort's original binary-analysis reports 24 AppKit imports and a game that renders its
own interface; that is not an equivalent compatibility workload. Imported class counts
are not implementation estimates: each class can expose many required methods,
subclassing contracts, notifications, archive encodings and rendering semantics.

Original Excel entitlements name UBF8T346G9 Office app groups, Microsoft's identity
keychain group, Mac sandbox filesystem exceptions and the privileged licensing port.
A user-signed iPad app cannot simply keep Microsoft's entitlement grants. Apple documents
that the `<teamID>.<group>` Mac app-group format is unsupported on iPadOS and keychain
access groups are protected by signing/provisioning. This is an additional real auth/
storage compatibility problem; re-signing is not equivalent to preserving these grants.

## Mapping candidates — not implemented compatibility claims

| macOS API | Candidate iPad implementation | Required semantics before use |
| --- | --- | --- |
| NSScreen | UIScreen / UIWindowScene | Coordinate origin, points/backing scale, screen changes |
| NSWindow / NSView | Compatibility objects owning UIWindow / UIView | Class hierarchy, responder chain, drawing, invalidation, layout and nib decoding |
| NSEvent | Keyboard/pointer/touch bridge | Event ordering, focus, modifiers, text input/IME and selection |
| NSOpenPanel / NSSavePanel | UIDocumentPickerViewController and coordinated file access/export | Modal/completion contracts, security scope, atomic save and reopen |
| NSPasteboard | UIPasteboard | Formats including rich text, images and tabular data |
| NSMenu | UIMenu / explicit command model | Validation, keyboard equivalents and target/action dispatch |
| NSCursor | UIPointerInteraction | Pointer shape, region, enter/exit and drag behavior |
| NSWorkspace | Specific UIApplication/file APIs | Per-call behavior; no blanket success-returning stub |
| NSTextView / NSLayoutManager / NSGraphicsContext | Purpose-built text/drawing compatibility | No direct class alias or generic UIKit rename can satisfy these contracts |

No implementation is claimed for these classes yet. A diagnostics shim with a heartbeat
is present separately. Unknown ABI signatures are never synthesized.

## Known limits of M1

Static inventory and load dependency map are complete for the extracted files with zero
parser errors. Protocol-list entries are counted, not fully decoded into protocol method
contracts. Objective-C strings are extracted but selector callsites/types are not fully
reconstructed. Runtime dynamic loads, signing checks and optional-feature eager init
remain unknown. iOS SDK exported-symbol audit and device dyld checks are pending a Mac
runner/device. Accordingly M1 is a static checkpoint, not proof of loader compatibility.
