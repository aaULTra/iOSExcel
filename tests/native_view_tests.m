#import "ExcelView.h"
#import <objc/runtime.h>
#include <math.h>
static void Check(BOOL value,NSString *reason) { if (!value) @throw [NSException exceptionWithName:@"ViewTestFailure" reason:reason userInfo:nil]; }
static void Throws(void (^block)(void)) { BOOL raised=NO; @try { block(); } @catch(NSException *exception) { raised=YES; } Check(raised,@"Expected predictable rejection"); }
@interface EXFlippedContractView : NSView @end
@implementation EXFlippedContractView
- (BOOL)isFlipped { return YES; }
@end
@interface EXLayoutContractView : NSView
@property(nonatomic) NSUInteger layouts;
@property(nonatomic,strong) NSMutableArray *moves;
@end
@implementation EXLayoutContractView
- (void)layout { self.layouts++; }
- (void)viewWillMoveToSuperview:(NSView *)view { if (!self.moves) self.moves=[NSMutableArray array]; [self.moves addObject:@[@"will",view?:NSNull.null]]; }
- (void)viewDidMoveToSuperview { [self.moves addObject:@[@"did",self.superview?:NSNull.null]]; }
@end
int main(int argc,const char **argv) {
 @autoreleasepool { @try {
    Check(argc==3,@"ABI input and report output required");
    NSView *root=[[NSView alloc] initWithFrame:CGRectMake(0,0,300,200)];
    NSView *child=[[NSView alloc] initWithFrame:CGRectMake(10,20,80,60)]; [root addSubview:child];
    Check(child.superview==root && child.nextResponder==root && root.subviews.count==1,@"Hierarchy ownership and responder chain must agree");
    Check(child.window==nil && !child.isFlipped,@"Unbound view has no fabricated NSWindow and defaults to bottom-left coordinates");
    Check(CGPointEqualToPoint([child convertPoint:CGPointZero toView:root],CGPointMake(10,20)),@"Unflipped child origin mapping incorrect");
    EXFlippedContractView *flipped=[[EXFlippedContractView alloc] initWithFrame:CGRectMake(100,40,100,80)];
    flipped.bounds=CGRectMake(5,7,200,160); [root addSubview:flipped];
    Check(CGPointEqualToPoint([flipped convertPoint:CGPointMake(5,7) toView:root],CGPointMake(100,120)),@"Flipped origin must map to the top of the frame");
    Check(CGPointEqualToPoint([flipped convertPoint:CGPointMake(205,167) toView:root],CGPointMake(200,40)),@"Scaled flipped bounds mapping incorrect");
    CGPoint other=[child convertPoint:CGPointZero toView:flipped];
    Check(CGPointEqualToPoint(other,CGPointMake(-175,207)),@"Sibling conversion must account for scaling and opposite origins");
    Check(CGPointEqualToPoint([flipped convertPoint:other toView:child],CGPointZero),@"Sibling point conversion must round-trip");
    Check(CGRectEqualToRect([flipped convertRect:flipped.bounds toView:root],flipped.frame),@"Rect conversion must normalize flipped corners");
    Check(CGRectEqualToRect([flipped convertRect:flipped.frame fromView:root],flipped.bounds),@"Reverse rect conversion failed");
    EXFlippedContractView *nested=[[EXFlippedContractView alloc] initWithFrame:CGRectMake(1,2,10,8)]; [child addSubview:nested];
    Check(CGPointEqualToPoint([nested convertPoint:CGPointZero toView:root],CGPointMake(11,30)),@"Nested transform order incorrect");
    child.bounds=CGRectMake(2,3,160,120); child.frame=CGRectMake(10,20,160,120);
    Check(CGRectEqualToRect(child.bounds,CGRectMake(2,3,320,240)),@"Frame resize must preserve prior bounds scaling and origin");
    [root addSubview:child]; Check(root.subviews.lastObject==child && root.subviews.count==2,@"Same-parent add should reorder without duplication");
    Throws(^{[nested addSubview:root];}); Throws(^{[root addSubview:root];});
    NSView *unrelated=[[NSView alloc] initWithFrame:CGRectMake(0,0,1,1)];
    Throws(^{(void)[child convertPoint:CGPointZero toView:unrelated];}); Throws(^{(void)[child convertPoint:CGPointZero toView:nil];});
    Throws(^{child.frame=CGRectMake(NAN,0,1,1);}); Throws(^{child.bounds=CGRectMake(0,0,-1,1);});
    NSView *zero=[NSView new]; [root addSubview:zero]; Throws(^{(void)[zero convertPoint:CGPointZero toView:root];}); [zero removeFromSuperview];
    EXLayoutContractView *layout=[[EXLayoutContractView alloc] initWithFrame:CGRectMake(0,0,5,5)]; [root addSubview:layout];
    Check(layout.moves.count==2,@"Move callbacks must fire in order");
    layout.needsLayout=YES; [root layoutSubtreeIfNeeded]; [root layoutSubtreeIfNeeded]; Check(layout.layouts==1,@"Layout must only run when invalidated");
    layout.hidden=YES; layout.needsDisplay=YES; Check(layout.isHidden && layout.needsDisplay,@"Visibility/display state incorrect");
    [layout removeFromSuperview]; Check(layout.superview==nil && layout.nextResponder==nil && layout.moves.count==4,@"Removal must detach responder chain and invoke callbacks");
    __weak NSView *weakChild;
    @autoreleasepool { NSView *temporary=[NSView new]; weakChild=temporary; [root addSubview:temporary]; }
    Check(weakChild!=nil,@"Parent must retain its children");
    @autoreleasepool { [weakChild removeFromSuperview]; }
    Check(weakChild==nil,@"Removing a child must release ownership without retaining a cycle");
    NSError *error=nil; NSArray *contract=[NSJSONSerialization JSONObjectWithData:[NSData dataWithContentsOfFile:@(argv[1])] options:0 error:&error]; Check(contract!=nil,error.localizedDescription);
    NSMutableArray *verified=[NSMutableArray array];
    for (NSDictionary *entry in contract) {
        Method method=class_getInstanceMethod(NSView.class,NSSelectorFromString(entry[@"selector"])); Check(method!=NULL,entry[@"selector"]);
        NSString *encoding=@(method_getTypeEncoding(method)); Check([encoding isEqual:entry[@"encoding"]],[@"ABI mismatch: " stringByAppendingString:entry[@"selector"]]); [verified addObject:entry];
    }
    NSDictionary *report=@{@"passed":@YES,@"abi_methods_verified":verified,@"scope":@"Native model geometry/hierarchy only; not UIKit drawing or Excel",@"checks":@[@"hierarchy and responder ownership",@"flipped/scaled/nested coordinate transforms",@"point/rect round trips",@"bounds scaling on resize",@"z-order without duplication",@"cycle rejection",@"unrelated/window conversion rejection",@"invalid/zero geometry rejection",@"move callbacks",@"layout invalidation",@"visibility/display flags",@"ARC ownership release"]};
    NSData *json=[NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:&error]; Check([json writeToFile:@(argv[2]) options:NSDataWritingAtomic error:&error],error.localizedDescription);
    puts("PASS: NSView hierarchy, responder ownership, flipped/scaled transforms, lifecycle/layout and exact AppKit ABI contracts. No Excel execution."); return 0;
 } @catch(NSException *exception) { fprintf(stderr,"FAIL: %s: %s\n",exception.name.UTF8String,exception.reason.UTF8String); return 1; } }
}
