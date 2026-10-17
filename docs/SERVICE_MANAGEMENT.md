# ServiceManagement first-failure investigation

Real loader run 39022585600 (020194501c9939f03282790d59168d91177df638)
passed SecurityInterface and stopped before entry at ServiceManagement.framework,
referenced by osf. Only osf in the selected 55-image closure directly loads this
framework. Exact imports: SMCopyAllJobDictionaries and kSMDomainUserLaunchd.
Their actual callers and startup necessity remain unobserved.

Native capture 39022987157 used MacOSX15.5 SDK declarations and the Mac runtime.
It confirmed CFArrayRef SMCopyAllJobDictionaries(CFStringRef) and the const CFStringRef
global. Its measured string value is exactly "kSMDomainUserLaunchd", its pointer
is eight bytes, and its data encoding is r^{__CFString=}. The function-pointer
encoding ^? alone does not establish an argument ABI; actual SDK declarations and
compiling the adapter against those declarations are required.
Evidence: service-management-declarations.json and service-management-values.json.
No launchd jobs were enumerated and no helper was invoked during capture.

Apple documents NULL as an error from this enumeration function and requires the
caller to release a successful array. The experimental adapter preserves the exact
constant and returns that error for every enumeration request. It does not return
an empty or fabricated job list, emulate a service, change authorization or provide
a licensing reply. It logs unavailable enumeration without logging domain contents.
No service submission/removal, helper launch or activation code is implemented.

The contract workflow compiles the definitions against Apple's actual declarations,
compares the native and adapter constant/type metadata, and requires NULL for the
known user domain, an invalid domain and a null domain. Native run 39023106574 passed declaration compilation, constant/data comparison and all three failure cases. The adapter is now integrated behind a seventh forwarding identity; UIKit run 39023211932 passed the constant and all three error checks inside the real UIKit test host. Actual loader 39023211961 passed this dependency and stopped at /usr/lib/swift/libswiftAppKit.dylib before Microsoft entry. A caller that requires successful job
enumeration must fail; later caller behavior is not replaced with success.

This import alone does not establish that job enumeration performs Office licensing.
The separately confirmed licensingV2 Mach-service/helper dependencies remain
unresolved. No legitimate iPadOS activation path has been demonstrated.

Primary references:
- https://developer.apple.com/documentation/servicemanagement/smcopyalljobdictionaries(_:)
- https://developer.apple.com/documentation/servicemanagement/ksmdomainuserlaunchd
