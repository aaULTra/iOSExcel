# Explicit zero-import optional-load experiments

This policy is explicitly limited to the previously observed real loader failure:
`ExceptionHandling.framework`. It is not a blanket rule for missing frameworks.

Evidence at ea11fa5aae2508d17a0f5d529d0ebefbcaa0b191:

- Actual Excel loader aborted on its versioned path (38987517689 and 38988363346).
- Same-runtime canonical preflight failed, reporting no file/cache counterpart.
- Only Excel main links it in the recorded 55-image closure.
- There are no direct undefined symbols attributed to it, no NSExceptionHandler
  imports elsewhere, and none of its configuration selectors in the recorded
  selector inventory. Dynamic string construction cannot be excluded by this.
- Apple's documentation describes Objective-C exception monitoring/debugging
  through NSExceptionHandler, distinct from Foundation exception objects and C++
  unwinding. Those language/runtime dependencies are retained unchanged.

The experiment changes the one ordinary LC_LOAD_DYLIB command to
LC_LOAD_WEAK_DYLIB. It does not remove or renumber a dependency, alter code,
change bind streams, fabricate an API, suppress license validation or invent a
successful exception-monitoring result. Original paths/versions remain intact.

## Required guards

`weaken_unused_loads` requires two-level namespace, an actual symbol table and a
recognized classic dyld-info layout. Both undefined symbols and the actual bind,
weak-bind and lazy-bind streams must show zero references to the selected library.
Flat lookup prevents the experiment; unknown/threaded/chained formats fail safely.
All changes are limited to the logged four-byte command-kind field, with bytewise
verification that the rest of the image is identical before re-signing.

The runtime driver additionally requires an explicit per-framework allowlist,
recorded failure/preflight evidence, zero recorded imports/selectors, and a failed
canonical preflight in the current Simulator. Other frameworks are rejected by
the policy validator until separately investigated and intentionally implemented.
NetFS was added separately after the evidence below; it does not inherit a
blanket optional status merely because a framework is absent.

Unit safety tests cover a binding absent from the ordinary symbol table, ordinary
symbol use without a bind stream, flat lookup, malformed/unknown opcodes, stream
bounds, ordinal attribution and exact modification windows. They are not Excel
execution evidence. The real experiment in run 38989112909 passed the guards,
changed only the main executable load command, and advanced the first loader
failure to Kerberos.framework. Microsoft entry remained unconfirmed.
See docs/evidence/optional-exception-load.json for actual modification metadata.

Omitting optional framework initialization may still uncover a dynamic use or
another failure. No application or workbook milestone follows from a successful
flag change. The next actual runtime failure remains the next debugging target.

Primary references:
https://developer.apple.com/documentation/exceptionhandling/
https://github.com/apple-oss-distributions/xnu/blob/main/EXTERNAL_HEADERS/mach-o/loader.h
https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/dlopen_preflight.3.html

## NetFS experiment, not yet run

The actual first failure in 39019181596 is NetFS after the genuine Kerberos bridge.
Only main loads it; there are zero attributed imports and no NetFS undefined names
anywhere in the measured startup closure, including under other framework ordinals.
The canonical runtime preflight is false. No network mounting or authentication
API is replaced. Actual current undefined/bind tables must independently pass the
same zero-use guard before changing only LC_LOAD_DYLIB to LC_LOAD_WEAK_DYLIB.
NetFS-specific initialization and dynamic string lookups remain unproven.
Failure evidence is docs/evidence/real-loader-after-kerberos.json.
