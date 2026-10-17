#import <Foundation/Foundation.h>
#if EXCELSHIM_SHAPE_BASELINE
#import <ApplicationServices/ApplicationServices.h>
#else
#import "ExcelApplicationServices.h"
#endif
#include <math.h>
#include <limits.h>

static NSArray *Bounds(HIShapeRef shape) {
    if (HIShapeIsEmpty(shape)) return @[];
    CGRect bounds = CGRectZero;
#if EXCELSHIM_SHAPE_BASELINE
    HIShapeGetBounds(shape, &bounds);
#else
    bounds = CGPathGetPathBoundingBox((CGPathRef)shape);
#endif
    // Only the three imported shape operations are implemented. Compare region
    // geometry, not the raw representation of unimplemented HIShapeGetBounds.
    bounds = CGRectStandardize(bounds);
    return @[@(bounds.origin.x), @(bounds.origin.y), @(bounds.size.width), @(bounds.size.height)];
}
static NSDictionary *Observe(HIShapeRef shape) {
    if (!shape) @throw [NSException exceptionWithName:@"TestFailure" reason:@"Shape allocation failed" userInfo:nil];
    return @{@"empty": @(HIShapeIsEmpty(shape)), @"bounds": Bounds(shape)};
}
int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 2) return 2;
        CGRect inputs[] = {
            {{0,0},{10,10}}, {{5,3},{10,8}}, {{10,0},{2,10}}, {{30,30},{2,2}},
            {{1.25,-2.5},{4.5,8.25}}, {{2.5,-1.25},{6.75,4.5}}, {{0,0},{0,10}},
            {{5,6},{-3,-4}}, {{-10,-10},{4,6}},
            {{0.1,0.1},{0.2,0.2}}, {{0.7,0.7},{0.2,0.2}},
            {{0.2,0.2},{3.6,3.6}}, {{1.1,1.1},{0.5,0.5}},
            {{0.3,0.3},{3.4,3.4}}, {{-0.8,-0.8},{0.2,0.2}}, {{0.4,0.4},{0.2,0.2}}
        };
        NSUInteger pairs[][2] = {{0,1},{0,2},{0,3},{4,5},{0,6},{0,7},{8,0},
            {9,10},{11,12},{12,11},{0,12},{12,0},{4,4},{9,9},{13,11},{14,15}};
        NSMutableArray *shapes = [NSMutableArray array], *intersections = [NSMutableArray array];
        for (NSUInteger i=0; i<sizeof(inputs)/sizeof(inputs[0]); i++) {
            HIShapeRef shape = HIShapeCreateWithRect(&inputs[i]);
            [shapes addObject:Observe(shape)]; CFRelease(shape);
        }
        for (NSUInteger i=0; i<sizeof(pairs)/sizeof(pairs[0]); i++) {
            HIShapeRef a=HIShapeCreateWithRect(&inputs[pairs[i][0]]), b=HIShapeCreateWithRect(&inputs[pairs[i][1]]);
            HIShapeRef intersection=HIShapeCreateIntersection(a,b);
            [intersections addObject:Observe(intersection)];
            CFRelease(intersection); CFRelease(a); CFRelease(b);
        }
#if !EXCELSHIM_SHAPE_BASELINE
#define REQUIRE(C) do { if (!(C)) @throw [NSException exceptionWithName:@"TestFailure" reason:@#C userInfo:nil]; } while (0)
        REQUIRE(EXPrintNotImplemented == kPMNotImplemented);
        REQUIRE(EXServiceNotImplemented == unimpErr);
        PMPrintSession session=(PMPrintSession)(uintptr_t)1;
        REQUIRE(PMCreateSession(&session)==kPMNotImplemented && session==NULL);
        CGContextRef context=(CGContextRef)(uintptr_t)1;
        REQUIRE(PMSessionGetCGGraphicsContext((PMPrintSession)(uintptr_t)1,&context)==kPMNotImplemented && context==NULL);
        PMRect rect={1,2,3,4};
        REQUIRE(PMGetAdjustedPageRect((PMPageFormat)(uintptr_t)1,&rect)==kPMNotImplemented);
        REQUIRE(rect.top==0 && rect.left==0 && rect.bottom==0 && rect.right==0);
        PasteboardRef pasteboard=(PasteboardRef)(uintptr_t)1;
        REQUIRE(PasteboardCreate(NULL,&pasteboard)==unimpErr && pasteboard==NULL);
        EXDesktopItemCount count=ULONG_MAX;
        REQUIRE(PasteboardGetItemCount((PasteboardRef)(uintptr_t)1,&count)==unimpErr && count==0);
        BOOL trapped=NO;
        @try { PasteboardSynchronize((PasteboardRef)(uintptr_t)1); } @catch (NSException *exception) { trapped=[exception.name isEqualToString:@"ExcelShimUnsupportedApplicationServices"]; }
        REQUIRE(trapped);
        trapped=NO;
        @try { HIShapeIsEmpty((HIShapeRef)CFSTR("foreign")); } @catch (NSException *exception) { trapped=[exception.name isEqualToString:@"ExcelShimUnsupportedApplicationServices"]; }
        REQUIRE(trapped);
#endif
        NSDictionary *report=@{@"shapes":shapes, @"intersections":intersections};
        NSError *error=nil;
        NSData *data=[NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:&error];
        if (!data || ![data writeToFile:[NSString stringWithUTF8String:argv[1]] options:NSDataWritingAtomic error:&error]) return 3;
        return 0;
    }
}
