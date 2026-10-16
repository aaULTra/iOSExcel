#import "ExcelScreenInternal.h"
#import "ExcelShim.h"
#include <math.h>
#if TARGET_OS_IOS
#import <UIKit/UIKit.h>
#endif

NSString *const NSDeviceSize=@"NSDeviceSize";
NSString *const NSDeviceIsScreen=@"NSDeviceIsScreen";
NSString *const NSDeviceResolution=@"NSDeviceResolution";
static id<EXScreenMetricsProvider> EXProvider;
static NSScreen *EXCurrentScreen;
static void EXScreenFail(NSString *reason) __attribute__((noreturn));
static void EXScreenFail(NSString *reason) {
    ExcelShimLog([@"NSScreen: " stringByAppendingString:reason]);
    @throw [NSException exceptionWithName:NSInternalInconsistencyException reason:reason userInfo:nil];
}
static void EXScreenRequireMain(void) {
    if (!NSThread.isMainThread) EXScreenFail(@"Screen access must occur on the main thread");
}
static BOOL EXFiniteRect(CGRect rect) {
    return isfinite(rect.origin.x) && isfinite(rect.origin.y) && isfinite(rect.size.width) && isfinite(rect.size.height);
}
@interface NSScreen ()
@property(nonatomic,strong) id<EXScreenMetricsProvider> metrics;
@end
@implementation NSScreen
+ (NSArray<NSScreen *> *)screens {
    EXScreenRequireMain();
    if (!EXProvider.available) return @[];
    if (!EXCurrentScreen) { EXCurrentScreen=[NSScreen new]; EXCurrentScreen.metrics=EXProvider; }
    return @[EXCurrentScreen];
}
+ (NSScreen *)mainScreen { return self.screens.firstObject; }
- (CGRect)validatedBounds {
    EXScreenRequireMain();
    if (!self.metrics.available) EXScreenFail(@"Workspace is no longer attached to a scene");
    CGRect bounds=self.metrics.bounds;
    if (!EXFiniteRect(bounds) || bounds.size.width<=0 || bounds.size.height<=0) EXScreenFail(@"Invalid workspace bounds");
    return bounds;
}
- (CGRect)frame {
    CGRect bounds=[self validatedBounds];
    return CGRectMake(0,0,bounds.size.width,bounds.size.height);
}
- (CGRect)visibleFrame {
    CGRect bounds=[self validatedBounds], usable=self.metrics.usableBounds;
    if (!EXFiniteRect(usable) || usable.size.width<0 || usable.size.height<0) EXScreenFail(@"Invalid usable workspace bounds");
    usable=CGRectIntersection(bounds,usable);
    if (CGRectIsNull(usable)) EXScreenFail(@"Usable workspace does not intersect scene bounds");
    // UIKit is top-left; desktop screen coordinates are bottom-left, in points.
    return CGRectMake(usable.origin.x-bounds.origin.x,
                      CGRectGetMaxY(bounds)-CGRectGetMaxY(usable),usable.size.width,usable.size.height);
}
- (CGFloat)backingScaleFactor {
    (void)[self validatedBounds]; CGFloat scale=self.metrics.backingScale;
    if (!isfinite(scale) || scale<=0) EXScreenFail(@"Invalid workspace backing scale");
    return scale;
}
- (NSString *)localizedName { (void)[self validatedBounds]; return self.metrics.workspaceName; }
- (NSDictionary *)deviceDescription {
    CGSize size=self.frame.size;
    // No invented physical DPI or CG display/device identity is supplied.
    ExcelShimLog(@"NSScreen deviceDescription: physical resolution and NSScreenNumber unavailable for the virtual workspace");
    return @{NSDeviceSize:[NSValue valueWithBytes:&size objCType:@encode(CGSize)],NSDeviceIsScreen:@YES};
}
- (CGRect)convertRectToBacking:(CGRect)rect {
    CGFloat scale=self.backingScaleFactor;
    if (!EXFiniteRect(rect)) EXScreenFail(@"Non-finite rectangle in backing conversion");
    CGRect out=CGRectMake(rect.origin.x*scale,rect.origin.y*scale,rect.size.width*scale,rect.size.height*scale);
    if (!EXFiniteRect(out)) EXScreenFail(@"Backing conversion overflow"); return out;
}
- (CGRect)convertRectFromBacking:(CGRect)rect {
    CGFloat scale=self.backingScaleFactor;
    if (!EXFiniteRect(rect)) EXScreenFail(@"Non-finite rectangle in backing conversion");
    CGRect out=CGRectMake(rect.origin.x/scale,rect.origin.y/scale,rect.size.width/scale,rect.size.height/scale);
    if (!EXFiniteRect(out)) EXScreenFail(@"Backing conversion overflow"); return out;
}
@end
void EXScreenSetProvider(id<EXScreenMetricsProvider> provider) {
    EXScreenRequireMain(); if (EXProvider==provider) return;
    EXProvider=provider; EXCurrentScreen=nil;
}

#if TARGET_OS_IOS
@interface EXUIKitScreenMetrics : NSObject <EXScreenMetricsProvider>
@property(nonatomic,weak) UIWindow *window;
@end
@implementation EXUIKitScreenMetrics
- (BOOL)available { return self.window.windowScene!=nil; }
- (CGRect)bounds { return self.window.bounds; }
- (CGRect)usableBounds {
    UIWindow *window=self.window; UIViewController *controller=window.rootViewController;
    if (controller.isViewLoaded && controller.view.window==window)
        return [controller.view convertRect:controller.view.safeAreaLayoutGuide.layoutFrame toView:window];
    return UIEdgeInsetsInsetRect(window.bounds,window.safeAreaInsets);
}
- (CGFloat)backingScale { return self.window.windowScene.screen.scale; }
- (NSString *)workspaceName { return @"Excel iPad workspace"; }
@end
void ExcelShimAttachScreenToWindow(UIWindow *window) {
    EXScreenRequireMain();
    if ([EXProvider isKindOfClass:EXUIKitScreenMetrics.class] && ((EXUIKitScreenMetrics *)EXProvider).window==window) return;
    EXUIKitScreenMetrics *metrics=[EXUIKitScreenMetrics new]; metrics.window=window; EXScreenSetProvider(metrics);
    ExcelShimLog(@"NSScreen attached to the UIKit scene workspace");
}
#endif
