# Partial NSView hierarchy and drawing bridge

The selected startup closure imports NSView in 13 images. All 32 implemented method
names appear in its global selector strings; this is not receiver-specific callsite
attribution or evidence of execution. The compiled signatures are compared with captured
real arm64 AppKit metadata. See view-references-16.55.json and native-view-contracts.json.

## Object model and geometry

NSView remains a subclass of NSResponder, not an alias for UIView. It owns child model
views strongly, keeps a weak superview reference, and updates the logical nextResponder
chain when adding/removing children. Its UIKit projection owns a separate UIView whose
reference to the model is weak. Native views detach when their models are released.
Adding an ancestor/self is rejected; same-parent additions reorder without duplication.
Move callbacks and explicit layout invalidation are implemented.

Frame and bounds are separate, with positive axis-aligned scaling and arbitrary finite
bounds origins. Point/rect conversion across one model root supports mixed flipped and
unflipped descendants and normalizes reversed rectangle corners. Frame resizing preserves
existing bounds scaling. Invalid rectangles, non-finite projections, scaling overflow,
unrelated roots and non-invertible zero-size conversions fail with logged exceptions.
This is not support for rotations, arbitrary affine view transforms or cross-window
coordinate conversion.

A root can attach to an internal UIKit host. Model bottom-left parent coordinates are
converted to UIKit top-left placement, while bounds scaling is represented by the native
view's transform. Visibility and same-parent z-order changes propagate to UIKit.

The native drawing callback invokes the typed model drawRect: with the actual UIKit
CoreGraphics context. Its CTM and dirty rectangle adapt to isFlipped and bounds origins;
the graphics state is restored even if the subclass throws. A plain NSView draws nothing,
matching a transparent base view. Custom subclasses perform their own drawing. The
projection clips to bounds to match the selected pre-macOS-14 baseline; Apple's current
NSView default differs, so this is an explicit compatibility choice.

## Explicit limits

No NSWindow bridge is implemented. window returns nil because no compatibility window
is associated, and nil-view/window coordinate conversions raise rather than returning
invented positions. Internal host attachment is not a substitute NSWindow or an Excel
window manager. Parent/child window lifecycle notifications are not implemented.

Autolayout/constraints, autoresizing masks, arbitrary transforms, view archives/NSCoding,
hit testing and NSEvent/keyboard/IME delivery remain unimplemented. The layout callback
is manual invalidation, not an AppKit constraint solver. UIKit display scheduling is not
a full replacement for display/lockFocus or synchronous AppKit display APIs. No
NSGraphicsContext, NSColor, NSFont, text control or rich rendering semantics are supplied
by this change. Unknown APIs continue to fail through the existing exception/log path.

## Tests and scope

Native model tests cover hierarchy/responder ownership, mixed-origin scaled/nested
conversions, point/rect round trips, bounds scaling, z-order, cycle/invalid-input
rejection, lifecycle callbacks, layout invalidation and ARC ownership release. Thirty-two
compiled method encodings must match the captured AppKit contracts exactly.

The internal simulator host includes synthetic NSView subclasses that draw red regions
through actual UIKit callbacks. It checks placement, scaled bounds, coordinate agreement
with UIView, visibility/z-order/removal and four positive/negative pixel samples for
opposite coordinate origins. It contains no Microsoft code and no Excel UI. Only reports
are uploaded. Neither those fixtures nor native ABI comparisons establish M3 or M7 for
real Excel, activation, text rendering or workbook behavior.

Sources:
https://developer.apple.com/documentation/appkit/nsview/isflipped
https://developer.apple.com/documentation/appkit/nsview/convert(_:to:)-6u9ir
https://developer.apple.com/documentation/appkit/nsview/bounds
https://developer.apple.com/documentation/appkit/nsview/clipstobounds
https://developer.apple.com/documentation/appkit/nsview-drawing

## Verified checkpoint (2026-10-17 London)

Source c49197d20bae5005838e10b25fe5c69f5d382605 passed native workflow 38982725023
and simulator workflow 38982725046. Native tests matched all 32 selected method
encodings, including the overflow and ownership checks. The simulator was an iPad Pro
11-inch (M4) on 26.2. Each synthetic drawing subclass received a real drawRect: callback;
all four positive/negative red-pixel samples passed. Native hierarchy placement and
scaled model coordinates agreed with actual UIView conversion, and visibility, z-order
and removal checks passed. Screen/entry-bridge checks also remained green.

The signed shim now exports 16/538 required AppKit names and 6/143 imported classes,
including partial implementations. This is name coverage, not percentage compatibility.
The original 55-image retarget/forwarding checks also passed. Real Excel remains below
M3; no Office UI, workbook, activation or physical-device milestone is claimed.

Evidence is retained in native-view-contracts.json, view-simulator.json,
view-references-16.55.json and view-validation.json under docs/evidence. No test app,
Microsoft payload or unfinished IPA is published.
