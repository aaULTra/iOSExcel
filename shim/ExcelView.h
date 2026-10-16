#import "ExcelAppKit.h"
#import <CoreGraphics/CoreGraphics.h>
#import <TargetConditionals.h>
NS_ASSUME_NONNULL_BEGIN
@class NSWindow;
@interface NSView : NSResponder
- (instancetype)initWithFrame:(CGRect)frame;
@property(nonatomic) CGRect frame,bounds;
@property(nonatomic,readonly,nullable) NSView *superview;
@property(nonatomic,readonly,copy) NSArray<NSView *> *subviews;
@property(nonatomic,readonly,nullable) NSWindow *window;
@property(nonatomic,readonly) BOOL isFlipped;
@property(nonatomic,getter=isHidden) BOOL hidden;
@property(nonatomic) BOOL needsDisplay,needsLayout;
- (void)setFrameOrigin:(CGPoint)origin;
- (void)setFrameSize:(CGSize)size;
- (void)setBoundsOrigin:(CGPoint)origin;
- (void)setBoundsSize:(CGSize)size;
- (void)addSubview:(NSView *)view;
- (void)removeFromSuperview;
- (BOOL)isDescendantOf:(NSView *)view;
- (CGPoint)convertPoint:(CGPoint)point toView:(nullable NSView *)view;
- (CGPoint)convertPoint:(CGPoint)point fromView:(nullable NSView *)view;
- (CGRect)convertRect:(CGRect)rect toView:(nullable NSView *)view;
- (CGRect)convertRect:(CGRect)rect fromView:(nullable NSView *)view;
- (void)viewWillMoveToSuperview:(nullable NSView *)view;
- (void)viewDidMoveToSuperview;
- (void)drawRect:(CGRect)dirtyRect;
- (void)layout;
- (void)layoutSubtreeIfNeeded;
@end
#if TARGET_OS_IOS
@class UIView;
// Internal hosting boundary until an actual NSWindow bridge is implemented.
FOUNDATION_EXPORT void EXViewAttachRoot(NSView *view,UIView *host);
FOUNDATION_EXPORT UIView *EXViewNativeView(NSView *view);
#endif
NS_ASSUME_NONNULL_END
