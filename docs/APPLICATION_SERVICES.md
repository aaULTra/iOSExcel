# ApplicationServices: first actual missing compatibility library

The runtime-verified framework path repair advanced the real executable to
ApplicationServices in run 38986113826. Its canonical counterpart had no matching
Simulator SDK stub, so it was left unresolved. The measured closure has six load
commands for this framework and 40 distinct imported names.

All 40 function declarations were captured from Apple's actual arm64 MacOSX15.5
SDK in run 38986723308. Seventeen C type encodings and public error constants were
then captured by an original native program in run 38986987541. This records SDK
interface facts, not Microsoft execution or proof that all original callers use
every interface correctly. The desktop ItemCount ABI is 64-bit; it is kept under
an explicit compatibility typedef rather than assuming a mobile typedef matches.

## Source implementation and explicit limits

| Required group | Count | Behavior |
| --- | ---: | --- |
| HIShape | 3 | Create rectangle-backed CGPaths, intersect paths, query emptiness; only compatibility-created path objects supported |
| Core Printing | 27 | Log unsupported operations; return measured kPMNotImplemented (-30873), clear outputs; printer-ID query returns NULL |
| Carbon Pasteboard | 8 | Operations return unimpErr (-4) and clear outputs; synchronization raises because flags cannot encode an unsupported error |
| Universal Access zoom | 2 | Mac zoom feature explicitly disabled (logged false); focus-change logs and returns unimpErr; no iPad accessibility-status query claimed |

No printer session, print success, clipboard data or ownership is fabricated. The
printing and clipboard paths are deliberately unavailable, not functional adapters.
If real Excel initialization requires one, its first observed call/failure must
drive the next implementation. No licensing/authentication operation is changed.

Shapes retain CoreFoundation Create-rule ownership and may be released with
CFRelease. Foreign CF object types and unsupported/nonfinite geometry fail with
logged exceptions. This does not implement the full HIShape API or interoperability
with Apple's opaque macOS HIShape objects.

The loader adds a distinct ExcelApplicationServices.dylib facade reexporting the
existing shim. Its numeric version is measured from the actual load commands,
not guessed. Original import order and two-level indices remain unchanged.

## Validation gate

`tools/test_services.sh` runs a separate Apple-original shape executable and a
compatibility executable on the Mac runner, compares geometry/empty-region results,
checks explicit unsupported-output behavior and compares all 17 compatibility type
encodings with the measured SDK encodings. Native definitions compile against the
actual Apple declarations; iOS definitions compile with the measured desktop ABI.

At introduction these new tests and the real-loader retry are **pending**. A
successful compile, export or geometry check will not establish that Excel tolerates
unavailable printing/clipboard functionality. No Microsoft entry, initialization,
workbook, installed UIKit lifecycle or physical-device milestone is implied.

Primary interface/behavior references:
https://developer.apple.com/documentation/applicationservices/applicationservices_functions
https://developer.apple.com/documentation/applicationservices/core_printing
https://developer.apple.com/documentation/coregraphics/cgpathcreatecopybyintersectingpath

Measured declarations and type/value facts are under docs/evidence/application-services-*.

The first build (38987405047) caught an invalid proposed UIKit zoom-status mapping:
UIAccessibilityIsZoomEnabled is not declared in the selected SDK. The corrected
source explicitly disables the macOS zoom compatibility feature and logs that
choice. It does not assert that the iPad's own accessibility zoom is disabled.
