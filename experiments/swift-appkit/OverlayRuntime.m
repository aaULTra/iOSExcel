#import "ExcelOverlayTypes.h"
#import "ExcelShim.h"
#include <stdlib.h>
void ExcelSwiftOverlayUnavailable(const char *operation) {
    ExcelShimLog([@"UNIMPLEMENTED Swift AppKit overlay: " stringByAppendingString:@(operation)]);
    abort();
}
void ExcelSwiftOverlayDrawingUnavailable(CGRect rect, NSUInteger operation) {
    ExcelShimLog([NSString stringWithFormat:@"SWIFT_OVERLAY_DRAW %.17g %.17g %.17g %.17g %lu", (double)rect.origin.x, (double)rect.origin.y, (double)rect.size.width, (double)rect.size.height, (unsigned long)operation]);
    ExcelSwiftOverlayUnavailable("CGRect.fill(using:) drawing not implemented");
}
