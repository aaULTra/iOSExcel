# Research record — 2026-10-15

## Evidence discipline

Binary observations are static, not runtime results. Imported names are a lower bound
on the compatibility surface: dynamic lookup, Objective-C message dispatch, nib decoding,
plugins and helper launch paths add dependencies. Framework presence on iOS does not
prove that a macOS symbol or selector exists or has compatible semantics. No on-device
run or successful Microsoft activation has been observed.

## CyPort inspected FIRST

Repository https://github.com/Thijs2004/CyPort, main at
15b177ff16c2efc76639e1b7479a8fe7ce535f20 (2026-10-15).
Inspected README, build.sh, tools/ios_retarget.py, verify_build.sh,
MacShim.m, MacShimC.c, Launcher.swift and supporting store/cloud sources,
app/Info.plist, all three entitlement plists, docs/binary-analysis.md, commit history
and current issues #1 and #2. The upstream README reports gameplay on one iPhone;
that is an upstream claim, not independently reproduced evidence here. Older comments
and binary-analysis.md still call it untested; current code/README are the later state.

| Component | Reusable concept | Not transferable to Excel |
| --- | --- | --- |
| Retargeter | Thin arm64, edit LC_BUILD_VERSION, exact load paths, validate inputs | Pool/watchdog/free-hook byte patches, fixed engine offsets, automatic syscall reroutes |
| Two-level bindings | Library ordinals must remain consistent across symtab, bind opcodes and chained fixups | Collapsing AppKit/Carbon/etc. into one shim without complete ordinal handling |
| UIKit boot | Complete UIKit launch before expensive desktop startup; enter known entry path after foreground | Cyberpunk-specific sharedApplication interception and re-entry assumptions |
| AppKit wrappers | Explicit classes around UIKit host views/windows; bridge events | Metal-backed single-window game shell is not a desktop spreadsheet UI toolkit |
| Logging | Documents logs, first-failure runtime iteration | Generic unknown-selector q@: signatures, unsafe ABI guesses |
| Files | Container paths, Files picker and resource path auditing | REDengine data layout, 65 GB imports, case/SSD retry patches |
| Entitlements | Derive capabilities from measured requirements and profile | Copying 5 GB game's memory/address-space capabilities into Excel |
| Services | Identify optional features independently | Offline curl/Galaxy responses or account-success stubs; activation must remain real |
| Packaging | Native iOS bundle, re-sign nested code, zip Payload | Four top-level game dylibs is not Excel's recursive framework/helper structure |

CyPort leaves stale signatures after retargeting and re-signs at packaging. Its current
retargeter renumbers duplicate imports in both legacy bind streams and chained fixups.
This project deliberately does not merge dylib commands or apply instruction patches.

## Official source register

1. Microsoft release/download history:
   https://learn.microsoft.com/en-us/officeupdates/update-history-office-for-mac
   Download URLs were read from its live HTML, not guessed.
2. Apple silicon support:
   https://support.microsoft.com/en-gb/office/lifecycle/microsoft-365-office-2021-and-office-2019-support-for-apple-silicon
3. Microsoft deployment / license-selected feature sets:
   https://learn.microsoft.com/en-us/microsoft-365-apps/mac/deployment-options-for-office-for-mac
4. Serializer and device binding:
   https://learn.microsoft.com/en-us/microsoft-365-apps/mac/volume-license-serializer
5. Privileged activation helper:
   https://learn.microsoft.com/en-us/microsoft-365-apps/mac/licensing-helper-tool
6. Apple UI framework scope / main-thread requirements:
   https://developer.apple.com/documentation/technologyoverviews/uikit-appkit
7. Apple DTS: iOS apps may not spawn child processes:
   https://developer.apple.com/forums/thread/747499
8. UIKit launch sequence:
   https://developer.apple.com/documentation/uikit/about-the-app-launch-sequence
9. Document picker and clipboard mappings to investigate:
   https://developer.apple.com/documentation/uikit/uidocumentpickerviewcontroller
   https://developer.apple.com/documentation/uikit/uipasteboard

## Candidate rationale

16.53 (21091200) is the earliest LTSC 2021 release family supported by the supplied
serializer according to Microsoft. 16.55 (21111400) is a near-contemporary universal
candidate explicitly covered by Microsoft's Apple silicon documentation. Current
16.113.4 (26100421) is a comparator, not automatically the preferred port target.
Older is NOT assumed to mean fewer dependencies: the measured inventories decide.
No claim is made that the serializer grants a license or supports iPadOS; the user must
have a valid applicable entitlement, and OS/license compatibility remains unresolved.

All downloaded installers are official Microsoft-hosted non-App-Store packages.
Their signed contents have not been run. Linux static inspection does not substitute
for Apple's trust verification; the prepared macOS CI runs pkgutil --check-signature.

## Attached serializer observations

The XAR has two payloads: Office16_all_volume_licensing.pkg (346 cpio entries) and
Office16_all_licensing.pkg (6 entries). They contain Microsoft Office Setup Assistant,
its frameworks/error reporter, and licensingV2.helper with a launchd plist. No Excel.app.
The helper has a plain arm64 slice, platform macOS, minimum 11.0, SDK 11.3. It links
AppKit, Cocoa, DiskArbitration, IOKit, Security, ApplicationServices and CoreServices,
among other libraries. The launchd MachServices entry is
com.microsoft.office.licensingV2.helper.port; Program points to
/Library/PrivilegedHelperTools/com.microsoft.office.licensingV2.helper.
The helper imports Mac keychain APIs (including SecKeychainOpen and SecAccessCreate),
IORegistry APIs and DASessionCreate. These are measured imports, not proof of the
exact activation path taken on every launch.

Microsoft documents that the volume-license plist is encrypted using the boot drive
serial number and cannot be copied to another device. No license payloads, keys or
activation modifications are included in this project. No fake device serials or
activation-success stubs will be implemented.

## Completed experiment results

Three complete official Excel updater payloads extracted without executing Microsoft
code: 33,070 cpio entries (16.53), 33,014 (16.55), 44,279 (16.113.4).
Each full recursive Mach-O inventory completed with zero parser errors.
Installer hashes/sizes are in docs/evidence/installers.json.

16.55 LC_MAIN first instruction is an unconditional tail branch to an imported
NSApplicationMain stub; verified through LC_DYSYMTAB's indirect symbol table.
Info.plist names XLApplication and XLMainMenu. The exported-entry observation is
reproducible with tools/entry_probe.py, requiring no disassembler package.

M2 experiment changed four bytes in the main arm64 header (platform/minimum/SDK metadata).
The complete 41,983,228-byte __TEXT/__text section hash is unchanged. All 55 resolved
startup images separately accepted the same metadata transformation in memory. No
load path, activation logic, executable instruction, symbol binding or entrypoint was
patched. Original universal source bytes remain untouched. Whole-tree CLI correctly
refused an Intel-only file before creating output; this is expected and documented.

Thirteen tests passed, covering malformed/truncated metadata, FAT64 extraction,
CPU-label mismatch, archive traversal/symlinks, bounded gzip reading, exact metadata
mutation, iOS-vs-simulator SDK target filtering, ObjC exports and SDK reexports.
Workflow YAML, shell syntax and app plists parsed successfully. Objective-C compilation, Apple installer trust verification and the first iPhoneOS SDK
audit later succeeded on macOS CI (see below). Provisioning, installation and all
device/runtime tests remain unperformed.

Apple entitlement constraints checked against:
https://developer.apple.com/documentation/xcode/accessing-app-group-containers
https://developer.apple.com/documentation/security/sharing-access-to-keychain-items-among-a-collection-of-apps
The former explicitly excludes `<team identifier>.<group>` app groups from iPadOS.
The latter explains signing-protected keychain groups and missing-entitlement failures.
These constrain preserving Office identity storage under a user-signed bundle; they do
not by themselves prove every possible subscription activation design impossible.

## macOS CI results

Both compared legacy packages passed the corrected Apple installer assessment workflow:
https://github.com/aaULTra/iOSExcel/actions/runs/38816989758
The 16.55 package's SHA-256 matches the local inspection exactly. pkgutil reports a
Microsoft Developer ID Installer signature, trusted timestamp 2021-11-14 and trusted
notarization. The native otool/nm/lipo inventory was uploaded with analysis reports.

The iPhoneOS 18.5 SDK declaration audit found 3,432 required system-symbol names and
847 names not found in the parsed exports. Private/umbrella reexports are explicitly
unresolved where their stubs are absent. Therefore “not found” is not a device-absence
claim. Examples with no unresolved stub parses include 52 Security names and 32
CoreGraphics names not present in their parsed iOS exports, including Mac keychain/ACL
and desktop display APIs. Full results: ios-sdk-audit-16.55.json.

The standalone probe compiled and passed codesign verification:
https://github.com/aaULTra/iOSExcel/actions/runs/38816769202
Its executable and shim are platform iOS, native arm64, minimum 18.0, SDK 18.5.
No Microsoft image is bundled or loaded. No physical device run has been observed.

## Additional supplied DMG

MO_Cr2021.dmg was inspected read-only, without executing its contents. It contains one
LTSC_2021_VL_Serializer.pkg inside a third-party-named HFS+ volume. That package is
byte-identical to the earlier Microsoft_Office_LTSC_2021_VL_Serializer.pkg: 11,463,579
bytes, SHA-256 c6f1709711270370d007c170155e054c0ebc9e09fec085effa9a8c868f4ad0e1.
It contributes no Excel application binary and was not committed to the repository.

## Loader redirection experiment (2026-10-16 London)

Actual source measurements: 24/55 startup images load both AppKit and Cocoa; 68 load-path
strings in total reference those two frameworks. AppKit's recorded compatibility
requirement is 45.0.0, Cocoa's 1.0.0. The implemented two-facade topology preserves all
original dependency indices and the complete binding payloads. A native dyld fixture
with independent imports and removed original libraries passed, and the corresponding
iOS forwarding dylibs compiled and passed signature/identity/version checks.
The local and Mac reports for the 55 actual images were identical.

Apple's ld64 manual documents two-level namespace, reexport_library and dylib versions:
https://github.com/apple-oss-distributions/ld64/blob/main/doc/man/man1/ld-classic.1
Apple's own Ruby reexport packaging uses the same forwarding-library linker mechanism:
https://github.com/apple-oss-distributions/ruby/blob/main/reexport.sh
This is evidence for the mechanism, not evidence of Excel API compatibility.

## Partial NSScreen adapter (2026-10-17 London)

The actual 16.55 metadata identifies NSScreen class imports in Excel main and 16 other
startup images. Candidate method-name strings are present in the closure; their global
presence is not receiver-specific attribution. The adapter implements nine public
class/instance signatures selected from captured arm64 AppKit runtime contracts.
Native tests passed geometry, asymmetric safe areas, resize, backing scale, Objective-C
struct returns, invalid inputs, detachment and thread enforcement. All nine compiled
method encodings matched exactly. The signed iOS shim export audit now finds 14/538
required AppKit names and 5/143 required classes; these remain name-coverage counts.

The UIKit backend uses the attached window/scene, not UIScreen.mainScreen or fabricated
physical display IDs/DPI. A separate simulator workflow exercises the production entry
bridge with synthetic desktop resources. No Microsoft execution or device milestone
is inferred from these checks. See SCREEN.md and the saved native/reference reports.

The simulator check subsequently passed on an iPad Pro 11-inch (M4), runtime 26.2,
using the production entry bridge and UIKit window metrics with synthetic desktop
resources. The workspace measured 834 x 1210 points at scale 2, and a controlled bounds
change refreshed the same screen object to 625.5 x 1028.5 points. Real Stage Manager,
rotation, external displays and physical-iPad execution were not tested. The host's
initial Rect helper name collision with MacTypes was fixed before the successful run.
