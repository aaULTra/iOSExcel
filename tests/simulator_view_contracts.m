#import "simulator_view_contracts.h"
#import "ExcelView.h"
static void EXViewCheck(BOOL value,NSString *reason) { if (!value) @throw [NSException exceptionWithName:@"ViewSimulatorFailure" reason:reason userInfo:nil]; }
static NSArray *EXViewRect(CGRect rect) { return @[@(rect.origin.x),@(rect.origin.y),@(rect.size.width),@(rect.size.height)]; }
@interface EXDrawingContractView : NSView
@property(nonatomic) NSUInteger drawCalls;
@property(nonatomic) BOOL contextSeen;
@end
@implementation EXDrawingContractView
- (void)drawRect:(CGRect)dirtyRect {
    self.drawCalls++; CGContextRef context=UIGraphicsGetCurrentContext(); self.contextSeen=(context!=NULL);
    EXViewCheck(context!=NULL,@"Typed NSView draw callback needs the actual UIKit graphics context");
    CGContextSetRGBFillColor(context,1,0,0,1); CGContextFillRect(context,CGRectMake(0,0,20,15));
}
@end
@interface EXFlippedDrawingContractView : EXDrawingContractView @end
@implementation EXFlippedDrawingContractView
- (BOOL)isFlipped { return YES; }
@end
static BOOL EXViewRedPixel(UIImage *image,NSUInteger x,NSUInteger y) {
    CGImageRef cropped=CGImageCreateWithImageInRect(image.CGImage,CGRectMake(x,y,1,1)); EXViewCheck(cropped!=NULL,@"Pixel sample lies outside snapshot");
    uint8_t pixel[4]={0}; CGColorSpaceRef color=CGColorSpaceCreateDeviceRGB();
    CGContextRef context=CGBitmapContextCreate(pixel,1,1,8,4,color,kCGImageAlphaPremultipliedLast|kCGBitmapByteOrder32Big);
    EXViewCheck(context!=NULL,@"Pixel sampling context failed"); CGContextDrawImage(context,CGRectMake(0,0,1,1),cropped);
    CGContextRelease(context); CGColorSpaceRelease(color); CGImageRelease(cropped);
    return pixel[0]>200 && pixel[1]<30 && pixel[2]<30 && pixel[3]>200;
}
NSDictionary *EXRunUIKitViewContracts(UIWindow *window) {
    UIView *host=[[UIView alloc] initWithFrame:CGRectMake(20,30,200,160)]; host.backgroundColor=UIColor.whiteColor; [window.rootViewController.view addSubview:host];
    NSView *root=[[NSView alloc] initWithFrame:CGRectMake(0,0,200,160)];
    EXDrawingContractView *normal=[[EXDrawingContractView alloc] initWithFrame:CGRectMake(10,20,80,60)];
    EXFlippedDrawingContractView *flipped=[[EXFlippedDrawingContractView alloc] initWithFrame:CGRectMake(100,20,80,60)];
    [root addSubview:normal]; [root addSubview:flipped]; EXViewAttachRoot(root,host);
    UIView *nativeRoot=EXViewNativeView(root),*nativeNormal=EXViewNativeView(normal),*nativeFlipped=EXViewNativeView(flipped);
    EXViewCheck([NSView isSubclassOfClass:NSResponder.class] && ![(id)root isKindOfClass:UIView.class],@"NSView must preserve desktop inheritance rather than alias UIView");
    EXViewCheck(nativeRoot.superview==host && nativeNormal.superview==nativeRoot && nativeFlipped.superview==nativeRoot,@"Model and UIKit hierarchy must agree");
    EXViewCheck(CGRectEqualToRect(nativeNormal.frame,CGRectMake(10,80,80,60)) && CGRectEqualToRect(nativeFlipped.frame,CGRectMake(100,80,80,60)),@"Desktop bottom-left frame placement must convert into UIKit top-left placement");
    [host layoutIfNeeded]; [nativeNormal.layer setNeedsDisplay]; [nativeNormal.layer displayIfNeeded]; [nativeFlipped.layer setNeedsDisplay]; [nativeFlipped.layer displayIfNeeded];
    UIGraphicsImageRendererFormat *format=[UIGraphicsImageRendererFormat defaultFormat]; format.scale=1; format.opaque=YES;
    UIGraphicsImageRenderer *renderer=[[UIGraphicsImageRenderer alloc] initWithSize:host.bounds.size format:format];
    UIImage *image=[renderer imageWithActions:^(UIGraphicsImageRendererContext *context) { [host.layer renderInContext:context.CGContext]; }];
    EXViewCheck(normal.drawCalls>0 && flipped.drawCalls>0 && normal.contextSeen && flipped.contextSeen,@"Both flipped and unflipped NSView subclasses must actually draw");
    EXViewCheck(EXViewRedPixel(image,15,130) && !EXViewRedPixel(image,15,85),@"Unflipped drawing must land at the lower-left of the child, not UIKit's upper-left");
    EXViewCheck(EXViewRedPixel(image,105,85) && !EXViewRedPixel(image,105,130),@"Flipped drawing must preserve the upper-left origin");
    normal.hidden=YES; EXViewCheck(nativeNormal.hidden,@"NSView hidden state must reach UIKit"); normal.hidden=NO;
    flipped.bounds=CGRectMake(5,7,160,120);
    EXViewCheck(CGRectEqualToRect(nativeFlipped.bounds,CGRectMake(0,0,160,120)) && CGRectEqualToRect(nativeFlipped.frame,CGRectMake(100,80,80,60)),@"UIKit projection must retain frame while applying custom/scaled bounds");
    CGPoint local=CGPointMake(25,27),parent=[flipped convertPoint:local toView:root];
    CGPoint ui=[nativeFlipped convertPoint:CGPointMake(local.x-5,local.y-7) toView:nativeRoot];
    EXViewCheck(CGPointEqualToPoint(ui,CGPointMake(parent.x,root.bounds.size.height-parent.y)),@"Scaled model conversion must agree with actual UIView conversion");
    [root addSubview:normal]; EXViewCheck(nativeRoot.subviews.lastObject==nativeNormal,@"Same-parent z-order changes must reach UIKit");
    [normal removeFromSuperview]; EXViewCheck(nativeNormal.superview==nil && normal.nextResponder==nil,@"Removing a model view must detach UIKit and responder ownership");
    [host removeFromSuperview];
    return @{@"passed":@YES,@"scope":@"Synthetic NSView subclasses backed by actual UIKit; no Excel code/UI",@"unflipped_native_frame":EXViewRect(CGRectMake(10,80,80,60)),@"flipped_native_frame":EXViewRect(CGRectMake(100,80,80,60)),@"normal_draw_calls":@(normal.drawCalls),@"flipped_draw_calls":@(flipped.drawCalls),@"red_pixel_checks":@4,@"checks":@[@"desktop class hierarchy",@"UIKit hierarchy mirror",@"bottom-left frame placement",@"actual typed drawRect dispatch",@"flipped/unflipped pixel locations",@"scaled bounds and UIView conversion",@"hidden state",@"z-order",@"removal and responder detach"],@"excel_executed":@NO};
}
