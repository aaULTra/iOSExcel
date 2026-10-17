#import "ExcelOverlayTypes.h"
#import "ExcelShim.h"
#include <stdlib.h>
void ExcelSwiftOverlayUnavailable(const char *operation) {
    ExcelShimLog([@"UNIMPLEMENTED Swift AppKit overlay: " stringByAppendingString:@(operation)]);
    abort();
}
// The compiler/native marker contract is verified before any loader integration.
__attribute__((visibility("default")))
const unsigned char EXSwiftAppKitForceAnchor __asm__("__swift_FORCE_LOAD_$_swiftAppKit") = 0;
