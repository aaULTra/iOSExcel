#import "ExcelOverlayTypes.h"
#import "ExcelShim.h"
#include <stdlib.h>
void ExcelSwiftOverlayUnavailable(const char *operation) {
    ExcelShimLog([@"UNIMPLEMENTED Swift AppKit overlay: " stringByAppendingString:@(operation)]);
    abort();
}
