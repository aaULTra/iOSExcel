#import <Foundation/Foundation.h>
#import <CoreGraphics/CoreGraphics.h>
#import <TargetConditionals.h>
NS_ASSUME_NONNULL_BEGIN
// CGRect matches the captured arm64 AppKit NSRect ABI (including ObjC encoding).
@interface NSScreen : NSObject
+ (NSArray<NSScreen *> *)screens;
+ (nullable NSScreen *)mainScreen;
@property(nonatomic,readonly) CGRect frame;
@property(nonatomic,readonly) CGRect visibleFrame;
@property(nonatomic,readonly) CGFloat backingScaleFactor;
@property(nonatomic,readonly,copy) NSString *localizedName;
@property(nonatomic,readonly,copy) NSDictionary *deviceDescription;
- (CGRect)convertRectToBacking:(CGRect)rect;
- (CGRect)convertRectFromBacking:(CGRect)rect;
@end
FOUNDATION_EXPORT NSString *const NSDeviceSize;
FOUNDATION_EXPORT NSString *const NSDeviceIsScreen;
FOUNDATION_EXPORT NSString *const NSDeviceResolution;
#if TARGET_OS_IOS
@class UIWindow;
// The active window's scene is a virtual desktop workspace, not a physical display.
FOUNDATION_EXPORT void ExcelShimAttachScreenToWindow(UIWindow *window);
#endif
NS_ASSUME_NONNULL_END
