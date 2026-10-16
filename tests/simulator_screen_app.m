// Internal simulator host: synthetic principal/nib/delegate, no Office binary or UI.
#import <UIKit/UIKit.h>
#include <stdlib.h>
#import "ExcelAppKit.h"
#import "ExcelScreen.h"
static BOOL WillLaunch,DidLaunch,Started;
static void Check(BOOL condition,NSString *reason) { if (!condition) @throw [NSException exceptionWithName:@"ScreenSimulatorFailure" reason:reason userInfo:nil]; }
static NSArray *EXScreenRectValues(CGRect rect) { return @[@(rect.origin.x),@(rect.origin.y),@(rect.size.width),@(rect.size.height)]; }
static CGRect ExpectedVisible(UIWindow *window) {
    UIView *view=window.rootViewController.view;
    CGRect safe=[view convertRect:view.safeAreaLayoutGuide.layoutFrame toView:window];
    safe=CGRectIntersection(window.bounds,safe);
    return CGRectMake(safe.origin.x-window.bounds.origin.x,CGRectGetMaxY(window.bounds)-CGRectGetMaxY(safe),safe.size.width,safe.size.height);
}
static void Finish(NSDictionary *report,int result) {
    NSError *error=nil;
    NSURL *documents=[NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask].firstObject;
    NSData *data=[NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:&error];
    if (![data writeToURL:[documents URLByAppendingPathComponent:@"screen-simulator-result.json"] options:NSDataWritingAtomic error:&error]) {
        NSLog(@"Failed to write test result: %@",error); exit(2);
    }
    exit(result);
}
static void RunTests(void) {
    @try {
        Check(WillLaunch && DidLaunch && NSApp.isRunning && NSApp.isActive,@"Real UIKit bridge must load the synthetic nib and dispatch desktop callbacks");
        UIWindow *window=nil;
        for (UIScene *scene in UIApplication.sharedApplication.connectedScenes)
            if ([scene isKindOfClass:UIWindowScene.class] && ((UIWindowScene *)scene).keyWindow) { window=((UIWindowScene *)scene).keyWindow; break; }
        Check(window!=nil,@"UIKit must own a key window in an active scene");
        [window layoutIfNeeded]; [window.rootViewController.view layoutIfNeeded];
        NSScreen *screen=NSScreen.mainScreen; Check(screen!=nil && screen==NSScreen.screens.firstObject,@"Scene-backed NSScreen must exist");
        CGRect originalBounds=window.bounds,initial=screen.frame;
        CGFloat scale=window.windowScene.screen.scale;
        Check(CGRectEqualToRect(initial,CGRectMake(0,0,window.bounds.size.width,window.bounds.size.height)),@"NSScreen frame must match the actual window workspace");
        Check(screen.backingScaleFactor==scale,@"Backing scale must come from the actual scene screen");
        Check(CGRectEqualToRect(screen.visibleFrame,ExpectedVisible(window)),@"Initial UIKit safe area conversion incorrect");
        window.rootViewController.additionalSafeAreaInsets=UIEdgeInsetsMake(11,7,17,13);
        [window.rootViewController.view setNeedsLayout]; [window.rootViewController.view layoutIfNeeded];
        CGRect insetVisible=screen.visibleFrame;
        Check(CGRectEqualToRect(insetVisible,ExpectedVisible(window)) && insetVisible.size.width<initial.size.width && insetVisible.size.height<initial.size.height,@"Additional real UIKit safe-area insets must affect desktop visibleFrame");
        CGRect sample=CGRectMake(1.25,2.5,20,30),pixels=[screen convertRectToBacking:sample];
        Check(CGRectEqualToRect(pixels,CGRectMake(1.25*scale,2.5*scale,20*scale,30*scale)),@"UIKit scale must drive backing coordinates");
        Check(CGRectEqualToRect([screen convertRectFromBacking:pixels],sample),@"Backing conversion must round-trip in simulator");
        // Controlled UIKit bounds mutation, not a claim of a real Stage Manager/rotation event.
        window.bounds=CGRectMake(0,0,originalBounds.size.width*0.75,originalBounds.size.height*0.85);
        [window setNeedsLayout]; [window layoutIfNeeded]; [window.rootViewController.view layoutIfNeeded];
        Check(screen==NSScreen.mainScreen,@"NSScreen identity must survive a workspace size change");
        CGRect resized=screen.frame;
        Check(CGRectEqualToRect(resized,CGRectMake(0,0,window.bounds.size.width,window.bounds.size.height)) && !CGRectEqualToRect(initial,resized),@"Geometry must refresh after actual UIKit window bounds change");
        Check(CGRectEqualToRect(screen.visibleFrame,ExpectedVisible(window)),@"Safe area must refresh after UIKit bounds change");
        window.bounds=originalBounds; window.rootViewController.additionalSafeAreaInsets=UIEdgeInsetsZero;
        [window setNeedsLayout]; [window layoutIfNeeded];
        Finish(@{@"passed":@YES,@"scope":@"iPad Simulator, real UIKit + production entry bridge, synthetic desktop classes/nib; NO Excel loaded",@"system_version":UIDevice.currentDevice.systemVersion,@"initial_workspace":EXScreenRectValues(initial),@"inset_visible_frame":EXScreenRectValues(insetVisible),@"resized_workspace":EXScreenRectValues(resized),@"scene_scale":@(scale),@"checks":@[@"UIKit lifecycle and synthetic desktop startup",@"key scene window",@"scene-backed scale",@"safe areas",@"backing round-trip",@"live UIKit bounds change",@"stable screen identity"],@"excel_executed":@NO,@"physical_device_test":@NO},0);
    } @catch(NSException *exception) { Finish(@{@"passed":@NO,@"exception":exception.name,@"reason":exception.reason?:@"Unknown"},1); }
}
@interface EXTestApplication : NSApplication @end
@implementation EXTestApplication @end
@interface EXTestDocumentController : NSDocumentController @end
@implementation EXTestDocumentController @end
@interface EXTestDelegate : NSObject @end
@implementation EXTestDelegate
- (void)applicationWillFinishLaunching:(NSNotification *)notification { WillLaunch=YES; }
- (void)applicationDidFinishLaunching:(NSNotification *)notification { DidLaunch=YES; }
- (void)applicationDidBecomeActive:(NSNotification *)notification {
    if (Started) return; Started=YES;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(0.25*NSEC_PER_SEC)),dispatch_get_main_queue(),^{ RunTests(); });
}
@end
int main(int argc,const char **argv) { @autoreleasepool { return NSApplicationMain(argc,argv); } }
