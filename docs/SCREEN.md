# NSScreen workspace adapter

Excel main and 16 other images in the selected startup closure import NSScreen.
The binary metadata also contains the implemented selector names. Those method-name
strings are global: they do not establish receiver-specific callsites or prove that
Excel has executed any of these methods. See screen-references-16.55.json.

## Implemented contract

The adapter exposes the attached UIKit window as one virtual desktop workspace.
It does not pretend the application owns the entire physical iPad display. The
production UIKit entry bridge attaches its window before desktop initialization and
reattaches when that scene becomes active. The metrics provider holds the window weakly.

| Desktop API | Adapter behavior |
| --- | --- |
| +screens / +mainScreen | Current attached workspace; empty/nil when no scene is attached |
| frame | Current UIWindow bounds size in points, with a zero-origin virtual desktop |
| visibleFrame | Root view's actual UIKit safe-area rectangle, clipped to the window and converted from top-left to bottom-left coordinates |
| backingScaleFactor | Attached UIWindowScene.screen.scale; no deprecated UIScreen.mainScreen lookup |
| convertRectToBacking: / convertRectFromBacking: | Scale point positions and sizes into/out of backing pixels; reject invalid values or overflow |
| localizedName | Explicit virtual-workspace name, not a reported hardware model |
| deviceDescription | Actual workspace size and is-screen flag only; physical DPI and CG display identity omitted with logging |

The NSDeviceResolution key constant is exported because the original binary imports
it. No guessed DPI or synthetic display identifier is put into the dictionary.
This is a partial deviceDescription implementation, not full AppKit equivalence.
Unknown selectors continue to fail through Objective-C exceptions and the existing
startup/uncaught-exception logging. No generic ABI signatures or success values are
synthesized. Screen access requires the main thread.

The same screen object reads fresh metrics after a UIKit bounds/safe-area change.
This does not yet implement AppKit screen-change notifications, physical-display
enumeration, Spaces, color-space/depth APIs or a multi-monitor desktop topology.
A controlled UIKit bounds mutation is a test of live metric refresh, not evidence of
actual Stage Manager, rotation, external-display or physical-iPad behavior.

## Validation boundary

Native tests use a synthetic metric provider to cover nonzero source origins, asymmetric
safe areas, stable identity, resizing, fractional coordinate conversion, Objective-C
struct return, invalid metrics, arithmetic overflow, detachment and thread enforcement.
Nine compiled class/instance method type encodings are compared exactly with captured
real arm64 macOS AppKit runtime metadata. CGRect matches the captured NSRect ABI.

A separate internal simulator host uses the production NSApplicationMain -> UIKit scene
-> desktop nib/callback bridge with this project's synthetic principal/nib/delegate.
It tests actual UIKit safe areas, scene scale, key-window attachment and a controlled
UIWindow bounds change. It contains no Microsoft code, performs no Office activation
and renders no Excel UI. Only reports may be uploaded, never this unfinished test host
or an IPA. Even a passing run does not advance real Excel to M3/M6.

References:
https://developer.apple.com/documentation/appkit/nsscreen/main
https://developer.apple.com/documentation/appkit/nsscreen/frame
https://developer.apple.com/documentation/appkit/nsscreen/visibleframe
https://developer.apple.com/documentation/appkit/nsscreen/backingscalefactor
https://developer.apple.com/documentation/uikit/uiview/safearealayoutguide
https://developer.apple.com/documentation/uikit/uiscreen/main

## Verified checkpoint

Source b0afc140421a73803058279458c6b62a4c0a7b2d passed the full native workflow
38980441518 and iPad simulator workflow 38980441619. The simulator was an iPad Pro
11-inch (M4) running 26.2. UIKit reported an 834 x 1210 point workspace at scale 2.
The adapter reflected the controlled change to 625.5 x 1028.5 points with stable object
identity and returned the expected actual UIKit safe-area coordinates. These values
are measurements of the simulator workspace, not physical-iPad validation.

The first simulator host build failed because a helper named Rect collided with an
Apple MacTypes declaration. It was renamed with a project prefix and the complete
runtime check then passed. Cold simulator initialization took several minutes; no
passing result was inferred from compilation or app installation alone.

Evidence: native-screen-contracts.json, screen-simulator.json and
screen-references-16.55.json under docs/evidence. Current exact export coverage is in
shim-coverage-16.55.json. Both workflows publish reports only.
