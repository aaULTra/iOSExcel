# ScriptingBridge: unavailable automation prototype

Actual loader run 39020471588 stops on ScriptingBridge.framework before Microsoft
entry. The sole distinct measured import is SBApplication, referenced by main and
mso99. This nonzero import prohibits the optional-load policy.

Native capture run 39021122191 established SBApplication -> SBObject -> NSObject,
17 public SBApplication method declarations and 81 native own method encodings
across the two classes. No targets were instantiated or Apple events sent.
Selectors appearing in the global Office inventory are candidates only; that
inventory does not attribute every generic selector to ScriptingBridge callers.

The small prototype under experiments/scripting reports automation unavailable.
Three application factories and two initializers return nil and log the disabled
operation. No event target, running-app identity, permission, authentication result
or successful Apple event is fabricated. Unknown selectors log and raise a named
exception. This is explicitly not an Apple-event engine or full scripting support.
It has not yet been integrated into the Excel load graph.

The native validation compares the exact five method encodings and both superclass
relationships against the real Mac classes in separate processes, and checks that
the prototype cannot manufacture an automation target. No Apple framework with
the same class names is linked into the compatibility test process. The native
baseline only reads metadata. Results are pending.

Measured encodings: both init methods and currentApplication return @16@0:8;
applicationWithBundleIdentifier: is @24@0:8@16;
applicationWithProcessIdentifier: is @20@0:8i16 (a 32-bit PID).
Native captures: docs/evidence/scripting-bridge-values.json and
scripting-bridge-declarations.json. Actual Office callers may require different
behavior; only the next real runtime result can establish whether startup can
continue without automation. Workbook and activation milestones remain unproven.
