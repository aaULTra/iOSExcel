#import "ExcelScreenInternal.h"
#import <objc/runtime.h>
#include <math.h>
#include <float.h>
static void Check(BOOL value,NSString *reason) { if (!value) @throw [NSException exceptionWithName:@"ScreenTestFailure" reason:reason userInfo:nil]; }
static void Throws(void (^block)(void)) { BOOL raised=NO; @try { block(); } @catch(NSException *exception) { raised=YES; } Check(raised,@"Expected a predictable exception"); }
@interface EXTestMetrics : NSObject <EXScreenMetricsProvider>
@property(nonatomic) BOOL available;
@property(nonatomic) CGRect bounds,usableBounds;
@property(nonatomic) CGFloat backingScale;
@property(nonatomic,copy) NSString *workspaceName;
@end
@implementation EXTestMetrics @end
int main(int argc,const char **argv) {
    @autoreleasepool { @try {
        Check(argc==3,@"ABI input and report output required");
        EXScreenSetProvider(nil); Check(NSScreen.mainScreen==nil && NSScreen.screens.count==0,@"No scene must produce no fabricated display");
        EXTestMetrics *provider=[EXTestMetrics new]; provider.available=YES;
        provider.bounds=CGRectMake(10,20,400,300); provider.usableBounds=CGRectMake(30,60,350,240); provider.backingScale=2; provider.workspaceName=@"Contract workspace";
        EXScreenSetProvider(provider); NSScreen *screen=NSScreen.mainScreen;
        Check(screen==NSScreen.screens.firstObject,@"Screen identity must be stable"); EXScreenSetProvider(provider); Check(screen==NSScreen.mainScreen,@"Reattaching a provider must retain identity");
        Check(CGRectEqualToRect(screen.frame,CGRectMake(0,0,400,300)),@"Virtual workspace must be zero-origin points");
        Check(CGRectEqualToRect(screen.visibleFrame,CGRectMake(20,20,350,240)),@"Insets and vertical coordinate conversion incorrect");
        CGRect rect=CGRectMake(1.25,-2.5,10,20),backing=[screen convertRectToBacking:rect];
        Check(CGRectEqualToRect(backing,CGRectMake(2.5,-5,20,40)),@"Backing scale must apply to position and size");
        Check(CGRectEqualToRect([screen convertRectFromBacking:backing],rect),@"Backing round-trip failed");
        NSInvocation *invocation=[NSInvocation invocationWithMethodSignature:[screen methodSignatureForSelector:@selector(visibleFrame)]];
        invocation.selector=@selector(visibleFrame); [invocation invokeWithTarget:screen]; CGRect result=CGRectZero; [invocation getReturnValue:&result];
        Check(CGRectEqualToRect(result,screen.visibleFrame),@"Objective-C struct return ABI failed");
        provider.bounds=CGRectMake(0,0,300,500); provider.usableBounds=CGRectMake(0,30,300,450); provider.backingScale=3;
        Check(screen==NSScreen.mainScreen && CGRectEqualToRect(screen.frame,CGRectMake(0,0,300,500)),@"Resize must refresh metrics without replacing the screen");
        Check(CGRectEqualToRect(screen.visibleFrame,CGRectMake(0,20,300,450)) && screen.backingScaleFactor==3,@"Resized safe area or scale stale");
        NSDictionary *device=screen.deviceDescription; CGSize size=CGSizeZero; [device[NSDeviceSize] getValue:&size size:sizeof(size)];
        Check(CGSizeEqualToSize(size,CGSizeMake(300,500)) && [device[NSDeviceIsScreen] boolValue],@"Device dictionary workspace size incorrect");
        Check(!device[NSDeviceResolution] && !device[@"NSScreenNumber"],@"Unknown physical DPI or display identity must not be fabricated");
        provider.backingScale=0; Throws(^{(void)screen.backingScaleFactor;}); provider.backingScale=NAN; Throws(^{(void)screen.backingScaleFactor;}); provider.backingScale=3;
        Throws(^{(void)[screen convertRectToBacking:CGRectMake(DBL_MAX,0,1,1)];});
        provider.bounds=CGRectMake(0,0,-1,1); Throws(^{(void)screen.frame;}); provider.bounds=CGRectMake(0,0,300,500);
        provider.available=NO; Check(NSScreen.mainScreen==nil,@"Detached scene must disappear"); Throws(^{(void)screen.frame;}); provider.available=YES;
        dispatch_semaphore_t semaphore=dispatch_semaphore_create(0); __block BOOL rejected=NO;
        [NSThread detachNewThreadWithBlock:^{ @try { (void)NSScreen.screens; } @catch(NSException *exception) { rejected=YES; } dispatch_semaphore_signal(semaphore); }];
        Check(dispatch_semaphore_wait(semaphore,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC))==0 && rejected,@"Background access must fail before reading UIKit metrics");
        NSError *error=nil; NSDictionary *contract=[NSJSONSerialization JSONObjectWithData:[NSData dataWithContentsOfFile:@(argv[1])] options:0 error:&error]; Check(contract!=nil,error.localizedDescription);
        NSMutableArray *verified=[NSMutableArray array];
        for (NSString *kind in @[@"instance_methods",@"class_methods"]) {
            Class cls=[kind isEqual:@"class_methods"]?object_getClass(NSScreen.class):NSScreen.class;
            for (NSDictionary *entry in contract[kind]) {
                Method method=class_getInstanceMethod(cls,NSSelectorFromString(entry[@"selector"]));
                Check(method!=NULL,[@"Missing method: " stringByAppendingString:entry[@"selector"]]);
                NSString *encoding=@(method_getTypeEncoding(method)); Check([encoding isEqual:entry[@"encoding"]],[@"ABI mismatch: " stringByAppendingString:entry[@"selector"]]);
                [verified addObject:@{@"kind":kind,@"selector":entry[@"selector"],@"encoding":encoding}];
            }
        }
        NSDictionary *report=@{@"passed":@YES,@"abi_methods_verified":verified,@"scope":@"Synthetic geometry provider on native arm64 macOS; not UIKit or Excel execution",@"checks":@[@"absent scene",@"stable identity",@"safe-area vertical conversion",@"fractional backing scale round-trip",@"Objective-C struct return",@"live resize",@"no invented hardware identity",@"invalid metrics and overflow",@"disconnected scene",@"main-thread enforcement"]};
        NSData *json=[NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:&error]; Check([json writeToFile:@(argv[2]) options:NSDataWritingAtomic error:&error],error.localizedDescription);
        puts("PASS: NSScreen geometry, safe areas, resize, backing conversion, failure contracts and exact AppKit method encodings. No Excel execution."); return 0;
    } @catch(NSException *exception) { fprintf(stderr,"FAIL: %s: %s\n",exception.name.UTF8String,exception.reason.UTF8String); return 1; } }
}
