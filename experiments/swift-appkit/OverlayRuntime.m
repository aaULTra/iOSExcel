#import "ExcelOverlayTypes.h"
#import "ExcelShim.h"
#import <TargetConditionals.h>
#if !TARGET_OS_OSX
#import <UIKit/UIKit.h>
#endif
#include <math.h>
#include <stdlib.h>
#if defined(EXCEL_OVERLAY_TEST_CONTEXT)
static _Thread_local CGContextRef testContext;
void ExcelSwiftOverlaySetTestContext(CGContextRef context) { testContext = context; }
#endif
void ExcelSwiftOverlayUnavailable(const char *operation) {
    ExcelShimLog([@"UNIMPLEMENTED Swift AppKit overlay: " stringByAppendingString:@(operation)]);
    abort();
}
void ExcelSwiftOverlayDrawingUnavailable(CGRect rect, NSUInteger operation) {
    ExcelShimLog([NSString stringWithFormat:@"SWIFT_OVERLAY_DRAW %.17g %.17g %.17g %.17g %lu", (double)rect.origin.x, (double)rect.origin.y, (double)rect.size.width, (double)rect.size.height, (unsigned long)operation]);
    CGContextRef context = NULL;
#if defined(EXCEL_OVERLAY_TEST_CONTEXT)
    context = testContext;
#elif !TARGET_OS_OSX
    context = UIGraphicsGetCurrentContext();
#endif
    if (!context) ExcelSwiftOverlayUnavailable("CGRect.fill(using:) has no current graphics context");
    if (!isfinite(rect.origin.x) || !isfinite(rect.origin.y) || !isfinite(rect.size.width) || !isfinite(rect.size.height))
        ExcelSwiftOverlayUnavailable("CGRect.fill(using:) nonfinite rectangle");
    CGBlendMode mode;
    switch (operation) {
        case NSCompositingOperationCopy: mode = kCGBlendModeCopy; break;
        case NSCompositingOperationSourceOver: mode = kCGBlendModeNormal; break;
        default: ExcelSwiftOverlayUnavailable("CGRect.fill(using:) unmeasured compositing operation");
    }
    CGContextSaveGState(context);
    CGContextSetBlendMode(context, mode);
    CGContextFillRect(context, rect);
    CGContextRestoreGState(context);
}
