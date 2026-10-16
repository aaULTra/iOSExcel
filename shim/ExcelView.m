#import "ExcelView.h"
#import "ExcelShim.h"
#include <math.h>
#if TARGET_OS_IOS
#import <UIKit/UIKit.h>
@interface EXNativeView : UIView
@property(nonatomic,weak) NSView *owner;
@end
#endif
static void EXViewFail(NSString *reason) __attribute__((noreturn));
static void EXViewFail(NSString *reason) {
    ExcelShimLog([@"NSView: " stringByAppendingString:reason]);
    @throw [NSException exceptionWithName:NSInternalInconsistencyException reason:reason userInfo:nil];
}
static void EXViewMain(void) { if (!NSThread.isMainThread) EXViewFail(@"View access requires the main thread"); }
static BOOL FinitePoint(CGPoint p) { return isfinite(p.x)&&isfinite(p.y); }
static void ValidRect(CGRect r) {
    if (!FinitePoint(r.origin)||!isfinite(r.size.width)||!isfinite(r.size.height)||r.size.width<0||r.size.height<0) EXViewFail(@"Non-finite or negative view rectangle");
}
@interface NSView () {
    CGRect _frame,_bounds;
    __weak NSView *_parent;
    NSMutableArray<NSView *> *_children;
    BOOL _hidden,_needsDisplay,_needsLayout,_inLayout;
#if TARGET_OS_IOS
    EXNativeView *_native;
#endif
}
- (void)ex_compatSyncNative;
#if TARGET_OS_IOS
- (EXNativeView *)ex_compatNativeView;
- (void)ex_compatAttachHost:(UIView *)host;
#endif
@end
@implementation NSView
- (instancetype)init { return [self initWithFrame:CGRectZero]; }
- (instancetype)initWithFrame:(CGRect)frame {
    EXViewMain(); ValidRect(frame); self=[super init];
    if (self) { _frame=frame; _bounds=CGRectMake(0,0,frame.size.width,frame.size.height); _children=[NSMutableArray array]; _needsDisplay=YES; }
    return self;
}
- (CGRect)frame { EXViewMain(); return _frame; }
- (CGRect)bounds { EXViewMain(); return _bounds; }
- (void)setFrame:(CGRect)frame {
    EXViewMain(); ValidRect(frame); CGRect bounds=_bounds;
    bounds.size.width=_frame.size.width>0?_bounds.size.width*(frame.size.width/_frame.size.width):frame.size.width;
    bounds.size.height=_frame.size.height>0?_bounds.size.height*(frame.size.height/_frame.size.height):frame.size.height;
    ValidRect(bounds); _frame=frame; _bounds=bounds;
    [self ex_compatSyncNative]; self.needsDisplay=YES; self.needsLayout=YES;
}
- (void)setBounds:(CGRect)bounds { EXViewMain(); ValidRect(bounds); _bounds=bounds; [self ex_compatSyncNative]; self.needsDisplay=YES; self.needsLayout=YES; }
- (void)setFrameOrigin:(CGPoint)origin { CGRect frame=self.frame; frame.origin=origin; self.frame=frame; }
- (void)setFrameSize:(CGSize)size { CGRect frame=self.frame; frame.size=size; self.frame=frame; }
- (void)setBoundsOrigin:(CGPoint)origin { CGRect bounds=self.bounds; bounds.origin=origin; self.bounds=bounds; }
- (void)setBoundsSize:(CGSize)size { CGRect bounds=self.bounds; bounds.size=size; self.bounds=bounds; }
- (NSView *)superview { EXViewMain(); return _parent; }
- (NSArray<NSView *> *)subviews { EXViewMain(); return [_children copy]; }
- (NSWindow *)window { EXViewMain(); return nil; } // No NSWindow has been associated yet.
- (BOOL)isFlipped { return NO; }
- (BOOL)isHidden { EXViewMain(); return _hidden; }
- (void)setHidden:(BOOL)hidden { EXViewMain(); _hidden=hidden;
#if TARGET_OS_IOS
    _native.hidden=hidden;
#endif
}
- (BOOL)needsDisplay { EXViewMain(); return _needsDisplay; }
- (void)setNeedsDisplay:(BOOL)needed { EXViewMain(); _needsDisplay=needed;
#if TARGET_OS_IOS
    if (needed) [_native setNeedsDisplay];
#endif
}
- (BOOL)needsLayout { EXViewMain(); return _needsLayout; }
- (void)setNeedsLayout:(BOOL)needed { EXViewMain(); _needsLayout=needed;
#if TARGET_OS_IOS
    if (needed) [_native setNeedsLayout];
#endif
}
- (BOOL)isDescendantOf:(NSView *)view { EXViewMain(); for (NSView *p=self;p;p=p->_parent) if (p==view) return YES; return NO; }
- (void)addSubview:(NSView *)view {
    __attribute__((objc_precise_lifetime)) NSView *heldSelf=self; (void)heldSelf;
    __attribute__((objc_precise_lifetime)) NSView *heldChild=view; (void)heldChild;
    EXViewMain(); if (!view || view==self || [self isDescendantOf:view]) EXViewFail(@"View hierarchy cycle or invalid child");
    if (view->_parent==self) { [_children removeObjectIdenticalTo:view]; [_children addObject:view];
#if TARGET_OS_IOS
        [[self ex_compatNativeView] bringSubviewToFront:[view ex_compatNativeView]];
#endif
        return;
    }
    NSView *old=view->_parent; [view viewWillMoveToSuperview:self];
    if (view->_parent!=old || [self isDescendantOf:view]) EXViewFail(@"Reentrant hierarchy change during move callback");
    if (old) [old->_children removeObjectIdenticalTo:view];
    view->_parent=self; [_children addObject:view]; view.nextResponder=self;
#if TARGET_OS_IOS
    [[self ex_compatNativeView] addSubview:[view ex_compatNativeView]];
#endif
    [view ex_compatSyncNative]; [view viewDidMoveToSuperview]; self.needsLayout=YES;
}
- (void)removeFromSuperview {
    __attribute__((objc_precise_lifetime)) NSView *heldSelf=self; (void)heldSelf;
    EXViewMain(); NSView *old=_parent; if (!old) return;
    [self viewWillMoveToSuperview:nil]; if (_parent!=old) EXViewFail(@"Reentrant hierarchy change during removal");
    [old->_children removeObjectIdenticalTo:self]; _parent=nil;
    if (self.nextResponder==old) self.nextResponder=nil;
#if TARGET_OS_IOS
    [_native removeFromSuperview];
#endif
    [self viewDidMoveToSuperview]; old.needsLayout=YES;
}
- (void)viewWillMoveToSuperview:(NSView *)view {}
- (void)viewDidMoveToSuperview {}
- (void)drawRect:(CGRect)dirtyRect {} // A plain NSView is transparent; subclasses perform their drawing.
- (void)layout {}
- (void)layoutSubtreeIfNeeded {
    EXViewMain(); if (_inLayout) return; _inLayout=YES;
    @try { if (_needsLayout) { _needsLayout=NO; [self layout]; } for (NSView *child in self.subviews) [child layoutSubtreeIfNeeded]; }
    @finally { _inLayout=NO; }
}
- (NSView *)ex_compatRoot { NSView *root=self; while (root->_parent) root=root->_parent; return root; }
- (CGPoint)ex_compatPointToParent:(CGPoint)point inverse:(BOOL)inverse {
    CGRect f=_frame,b=_bounds;
    if (f.size.width<=0||f.size.height<=0||b.size.width<=0||b.size.height<=0) EXViewFail(@"Cannot convert through a zero-size view");
    BOOL flipped=(self.isFlipped!=(_parent?_parent.isFlipped:NO));
    CGFloat sx=f.size.width/b.size.width,sy=f.size.height/b.size.height;
    CGPoint out;
    if (!inverse) out=CGPointMake(f.origin.x+(point.x-b.origin.x)*sx,f.origin.y+(flipped?(CGRectGetMaxY(b)-point.y):(point.y-b.origin.y))*sy);
    else out=CGPointMake(b.origin.x+(point.x-f.origin.x)/sx,flipped?CGRectGetMaxY(b)-(point.y-f.origin.y)/sy:b.origin.y+(point.y-f.origin.y)/sy);
    if (!FinitePoint(out)) EXViewFail(@"View coordinate conversion overflow"); return out;
}
- (CGPoint)convertPoint:(CGPoint)point toView:(NSView *)view {
    EXViewMain(); if (!FinitePoint(point)) EXViewFail(@"Non-finite view point");
    if (!view) EXViewFail(@"View-to-window conversion requires the unfinished NSWindow bridge");
    if (view==self) return point;
    if ([self ex_compatRoot]!=[view ex_compatRoot]) EXViewFail(@"Coordinate conversion across unrelated roots is unsupported");
    for (NSView *node=self;node;node=node->_parent) point=[node ex_compatPointToParent:point inverse:NO];
    NSMutableArray<NSView *> *path=[NSMutableArray array]; for (NSView *node=view;node;node=node->_parent) [path addObject:node];
    for (NSView *node in path.reverseObjectEnumerator) point=[node ex_compatPointToParent:point inverse:YES]; return point;
}
- (CGPoint)convertPoint:(CGPoint)point fromView:(NSView *)view {
    EXViewMain(); if (!view) EXViewFail(@"Window-to-view conversion requires the unfinished NSWindow bridge");
    return [view convertPoint:point toView:self];
}
- (CGRect)convertRect:(CGRect)rect toView:(NSView *)view {
    ValidRect(rect); CGPoint a=[self convertPoint:rect.origin toView:view],b=[self convertPoint:CGPointMake(CGRectGetMaxX(rect),CGRectGetMaxY(rect)) toView:view];
    return CGRectMake(fmin(a.x,b.x),fmin(a.y,b.y),fabs(a.x-b.x),fabs(a.y-b.y));
}
- (CGRect)convertRect:(CGRect)rect fromView:(NSView *)view {
    EXViewMain(); if (!view) EXViewFail(@"Window-to-view rectangle conversion requires the unfinished NSWindow bridge");
    return [view convertRect:rect toView:self];
}
- (void)ex_compatSyncNative {
#if TARGET_OS_IOS
    if (_native) {
        CGRect f=_frame,b=_bounds; UIView *parent=_native.superview;
        if (parent) {
            CGRect pb=_parent?_parent.bounds:parent.bounds;
            CGFloat x=_parent?f.origin.x-pb.origin.x:pb.origin.x+f.origin.x;
            CGFloat y=_parent?(_parent.isFlipped?f.origin.y-pb.origin.y:CGRectGetMaxY(pb)-CGRectGetMaxY(f)):CGRectGetMaxY(pb)-CGRectGetMaxY(f);
            _native.transform=CGAffineTransformIdentity; _native.bounds=CGRectMake(0,0,b.size.width,b.size.height);
            _native.center=CGPointMake(x+f.size.width/2,y+f.size.height/2);
            _native.transform=CGAffineTransformMakeScale(b.size.width?f.size.width/b.size.width:1,b.size.height?f.size.height/b.size.height:1);
        }
        _native.hidden=_hidden;
    }
#endif
    for (NSView *child in self.subviews) [child ex_compatSyncNative];
}
#if TARGET_OS_IOS
- (EXNativeView *)ex_compatNativeView {
    EXViewMain(); if (!_native) {
        _native=[[EXNativeView alloc] initWithFrame:CGRectZero]; _native.owner=self; _native.opaque=NO; _native.backgroundColor=UIColor.clearColor; _native.contentMode=UIViewContentModeRedraw;
        for (NSView *child in self.subviews) [_native addSubview:[child ex_compatNativeView]];
    }
    return _native;
}
- (void)ex_compatAttachHost:(UIView *)host {
    EXViewMain(); if (_parent) EXViewFail(@"Only a root view can attach to a UIKit host");
    [host addSubview:self.ex_compatNativeView]; [self ex_compatSyncNative];
}
#endif
@end
#if TARGET_OS_IOS
@implementation EXNativeView
- (void)layoutSubviews { [super layoutSubviews]; [self.owner layoutSubtreeIfNeeded]; }
- (void)drawRect:(CGRect)rect {
    NSView *owner=self.owner; if (!owner) return;
    CGContextRef context=UIGraphicsGetCurrentContext(); if (!context) EXViewFail(@"UIKit drawing callback has no graphics context");
    CGRect bounds=owner.bounds,dirty=CGRectMake(rect.origin.x+bounds.origin.x,owner.isFlipped?rect.origin.y+bounds.origin.y:CGRectGetMaxY(bounds)-CGRectGetMaxY(rect),rect.size.width,rect.size.height);
    CGContextSaveGState(context);
    @try {
        if (owner.isFlipped) CGContextTranslateCTM(context,-bounds.origin.x,-bounds.origin.y);
        else { CGContextTranslateCTM(context,-bounds.origin.x,CGRectGetMaxY(bounds)); CGContextScaleCTM(context,1,-1); }
        owner.needsDisplay=NO; [owner drawRect:dirty];
    } @finally { CGContextRestoreGState(context); }
}
@end
void EXViewAttachRoot(NSView *view,UIView *host) { [view ex_compatAttachHost:host]; }
UIView *EXViewNativeView(NSView *view) { return [view ex_compatNativeView]; }
#endif
