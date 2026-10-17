# Kerberos first-failure investigation

Actual Excel loader run 38989112909 stops at Kerberos.framework before entry.
All five imports are strong imports at ordinal 48 in main; only main loads this
framework in the recorded closure. It cannot use the zero-import optional guard.

Run 39018366500 captured the actual MacOSX15.5 public declarations.
The free-host-realm function returns a 32-bit error code, unlike assumptions
based on other Kerberos implementations. The four functions use opaque context
pointers; no context internals need to be invented or copied.

The iPhoneOS18.5 public SDK has GSS, but no Kerberos umbrella/header or stub.
The first isolated audit selected Simulator 18.5, not the 26.2 runtime of the
Excel loader test. It found all four functions by dlsym on public GSS, with
dladdr locating their actual implementations in Apple's private Heimdal image.
The legacy GSS_C_NT_USER_NAME data symbol was absent. This is not a public
API availability claim, a device result, ABI validation or authentication proof.
The first report is preserved as docs/evidence/kerberos-audit-first.json.

The next audit selects the newest installed M4 iPad runtime numerically and
tests a forwarding adapter before modifying the Excel load graph.
It compares the legacy Mac OID descriptor bytes/layout against the public GSS
constant, compiles all four declarations against the actual Mac declarations,
and allocates/frees genuine provider contexts and localhost realm lists.
No credentials, credential-cache selection, account login, activation, server
authentication, Microsoft binary execution or validation bypass is involved.
Configuration-dependent realm lookup errors are recorded without converting
them into successful authentication.

The experimental adapter dynamically resolves all four functions through GSS
and requires a common Apple system provider with the exact current Mach-O
platform. Missing/changed providers return ENOSYS without fake context or realm
objects. Freeing a non-null context without its provider raises a logged error.
The legacy data export contains the genuine public GSS OID descriptor address;
it is not a fabricated authentication result.

Private implementation ABI may change on future iPadOS builds. Neither an
export lookup nor a context ownership test proves domain SSO, Office login or
license activation. Those remain separate unresolved runtime requirements.
Run 39018956591 (fc187656004de6528ead6d857245a7d59ca8527f) passed both
native and M4 iPad Simulator 26.2 contracts. The legacy OID has 10 bytes,
16-byte descriptor size and elements at byte offset 8. All four Simulator
function addresses resolve to the same platform-7 runtime Heimdal image.
Genuine contexts and localhost realm lists were allocated and freed successfully.
No authentication or Excel code ran in those contract tests.

The native guard initially rejected an actual zippered macOS(1)+Catalyst(6)
provider. Raw header diagnostics in run 39018881927 established that exact pair;
Apple dyld source explicitly supports it. The corrected guard recognizes that
pair as macOS, never iOS or Simulator, and rejects other mixed platform sets.

The next real loader attempt adds the distinct ExcelKerberos.dylib facade and
repeats the OID and genuine ownership gate on that exact Simulator before Excel
can spawn. No empty provider, generic successful stub or account bypass is used.
See docs/evidence/kerberos-audit.json and kerberos-*-contracts/compatibility JSON.
Actual Excel passage beyond this dependency is still pending.

Primary interface references:
https://developer.apple.com/documentation/gss
https://developer.apple.com/documentation/gss/kerberos-implementation
https://github.com/apple-oss-distributions/Heimdal/blob/main/lib/krb5/context.c
https://github.com/apple-oss-distributions/Heimdal/blob/main/lib/krb5/get_host_realm.c

https://github.com/apple-oss-distributions/dyld/blob/main/mach_o/UnsafeHeader.cpp
