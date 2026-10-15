#import <Foundation/Foundation.h>
NS_ASSUME_NONNULL_BEGIN
@interface NSResponder : NSObject
@property(nonatomic,weak,nullable) NSResponder *nextResponder;
- (BOOL)acceptsFirstResponder;
- (BOOL)becomeFirstResponder;
- (BOOL)resignFirstResponder;
@end

@interface NSApplication : NSResponder
@property(nonatomic,weak,nullable) id delegate;
@property(nonatomic,readonly) BOOL isRunning, isActive;
@property(nonatomic,strong,nullable) id mainMenu;
+ (instancetype)sharedApplication;
- (void)finishLaunching;
@end
FOUNDATION_EXPORT NSApplication * _Nullable NSApp;
FOUNDATION_EXPORT NSString *const NSApplicationWillFinishLaunchingNotification;
FOUNDATION_EXPORT NSString *const NSApplicationDidFinishLaunchingNotification;
FOUNDATION_EXPORT NSString *const NSApplicationDidBecomeActiveNotification;
FOUNDATION_EXPORT NSString *const NSApplicationWillResignActiveNotification;
FOUNDATION_EXPORT NSString *const NSApplicationDidResignActiveNotification;
FOUNDATION_EXPORT void ExcelShimSetApplicationActive(BOOL active);

@interface NSFontManager : NSObject
+ (instancetype)sharedFontManager;
@end
@interface NSDocumentController : NSObject
+ (instancetype)sharedDocumentController;
@property(nonatomic,readonly) NSArray *documents;
- (void)addDocument:(id)document;
- (void)removeDocument:(id)document;
@end

// Called only after UIKit has launched, or by the Foundation-only contract test.
// Contents contains the ORIGINAL Info.plist and Resources; it is not the iOS bundle.
FOUNDATION_EXPORT BOOL ExcelShimStartDesktopApplication(NSURL *contents, NSError **error);
// Shim for Excel's measured LC_MAIN tail-call. It starts UIKit once; no main re-entry.
FOUNDATION_EXPORT int NSApplicationMain(int argc, const char * _Nullable const * _Nonnull argv);
NS_ASSUME_NONNULL_END
