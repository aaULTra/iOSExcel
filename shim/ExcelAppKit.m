#import "ExcelAppKit.h"
#import "ExcelNibArchive.h"
#import "ExcelShim.h"
#import <TargetConditionals.h>
#import <objc/message.h>
#if TARGET_OS_IOS
#import <UIKit/UIKit.h>
#endif

NSApplication *NSApp=nil;
NSString *const NSApplicationWillFinishLaunchingNotification=@"NSApplicationWillFinishLaunchingNotification";
NSString *const NSApplicationDidFinishLaunchingNotification=@"NSApplicationDidFinishLaunchingNotification";
NSString *const NSApplicationDidBecomeActiveNotification=@"NSApplicationDidBecomeActiveNotification";
NSString *const NSApplicationWillResignActiveNotification=@"NSApplicationWillResignActiveNotification";
NSString *const NSApplicationDidResignActiveNotification=@"NSApplicationDidResignActiveNotification";
static BOOL EXActive, EXNotifiedActive;
static NSArray *EXTopLevelObjects;
static void EXRequireMainThread(void) {
    if (!NSThread.isMainThread) @throw [NSException exceptionWithName:NSInternalInconsistencyException reason:@"AppKit compatibility startup requires the main thread" userInfo:nil];
}
@implementation NSResponder
- (BOOL)acceptsFirstResponder { return NO; }
- (BOOL)becomeFirstResponder { return YES; }
- (BOOL)resignFirstResponder { return YES; }
@end
@implementation NSApplication { BOOL _running, _launching; __weak id _delegate; }
+ (instancetype)sharedApplication {
    EXRequireMainThread();
    if (NSApp) {
        if (![NSApp isKindOfClass:self]) @throw [NSException exceptionWithName:NSInternalInconsistencyException reason:@"Application singleton was created with a different principal class" userInfo:nil];
        return (id)NSApp;
    }
    NSApp=[[self alloc] init]; return (id)NSApp;
}
- (id)delegate { return _delegate; }
- (void)setDelegate:(id)delegate {
    EXRequireMainThread();
    NSArray *names=@[NSApplicationWillFinishLaunchingNotification,NSApplicationDidFinishLaunchingNotification,NSApplicationDidBecomeActiveNotification,NSApplicationWillResignActiveNotification,NSApplicationDidResignActiveNotification];
    NSArray *selectors=@[@"applicationWillFinishLaunching:",@"applicationDidFinishLaunching:",@"applicationDidBecomeActive:",@"applicationWillResignActive:",@"applicationDidResignActive:"];
    NSNotificationCenter *center=NSNotificationCenter.defaultCenter;
    for (NSUInteger i=0;i<names.count;i++) {
        if (_delegate) [center removeObserver:_delegate name:names[i] object:self];
        SEL selector=NSSelectorFromString(selectors[i]);
        if ([delegate respondsToSelector:selector]) [center addObserver:delegate selector:selector name:names[i] object:self];
    }
    _delegate=delegate;
}
- (BOOL)isRunning { return _running; }
- (BOOL)isActive { return EXActive; }
- (void)finishLaunching {
    EXRequireMainThread(); if (_running || _launching) return; _launching=YES;
    ExcelShimLog(@"AppKit startup: willFinishLaunching");
    [NSNotificationCenter.defaultCenter postNotificationName:NSApplicationWillFinishLaunchingNotification object:self];
    [NSNotificationCenter.defaultCenter postNotificationName:NSApplicationDidFinishLaunchingNotification object:self];
    _running=YES; _launching=NO; ExcelShimLog(@"AppKit startup: didFinishLaunching callbacks returned");
}
@end
void ExcelShimSetApplicationActive(BOOL active) {
    EXRequireMainThread();
    if (!NSApp.isRunning) { EXActive=active; return; }
    if (EXNotifiedActive==active) { EXActive=active; return; }
    if (!active) [NSNotificationCenter.defaultCenter postNotificationName:NSApplicationWillResignActiveNotification object:NSApp];
    EXActive=active; EXNotifiedActive=active;
    [NSNotificationCenter.defaultCenter postNotificationName:active?NSApplicationDidBecomeActiveNotification:NSApplicationDidResignActiveNotification object:NSApp];
}
@implementation NSFontManager
+ (instancetype)sharedFontManager {
    EXRequireMainThread(); static NSFontManager *manager;
    if (!manager) manager=[[self alloc] init]; return (id)manager;
}
@end
@implementation NSDocumentController { NSMutableArray *_documents; }
+ (instancetype)sharedDocumentController {
    EXRequireMainThread(); static NSDocumentController *controller;
    if (controller && ![controller isKindOfClass:self]) @throw [NSException exceptionWithName:NSInternalInconsistencyException reason:@"Document controller singleton class mismatch" userInfo:nil];
    if (!controller) controller=[[self alloc] init]; return (id)controller;
}
- (instancetype)init { self=[super init]; if (self) _documents=[NSMutableArray array]; return self; }
- (NSArray *)documents { return [_documents copy]; }
- (void)addDocument:(id)document { EXRequireMainThread(); if (document && ![_documents containsObject:document]) [_documents addObject:document]; }
- (void)removeDocument:(id)document { EXRequireMainThread(); if (document) [_documents removeObjectIdenticalTo:document]; }
@end

BOOL ExcelShimStartDesktopApplication(NSURL *contents, NSError **error) {
    @try {
        EXRequireMainThread();
        if (!contents.isFileURL) @throw [NSException exceptionWithName:NSInvalidArgumentException reason:@"Desktop Contents must be a file URL" userInfo:nil];
        NSData *infoData=[NSData dataWithContentsOfURL:[contents URLByAppendingPathComponent:@"Info.plist"] options:0 error:error]; if (!infoData) return NO;
        NSDictionary *info=[NSPropertyListSerialization propertyListWithData:infoData options:NSPropertyListImmutable format:NULL error:error];
        if (![info isKindOfClass:NSDictionary.class]) @throw [NSException exceptionWithName:NSInvalidArgumentException reason:@"Invalid desktop Info.plist" userInfo:nil];
        NSString *principal=info[@"NSPrincipalClass"], *nib=info[@"NSMainNibFile"];
        if (![principal isKindOfClass:NSString.class] || ![nib isKindOfClass:NSString.class] || !principal.length || !nib.length || [nib containsString:@"/"] || [nib isEqual:@".."])
            @throw [NSException exceptionWithName:NSInvalidArgumentException reason:@"Missing or unsafe desktop principal class/main nib" userInfo:nil];
        Class cls=NSClassFromString(principal);
        if (!cls || ![cls isSubclassOfClass:NSApplication.class]) @throw [NSException exceptionWithName:NSInvalidArgumentException reason:[@"Desktop application class is unavailable: " stringByAppendingString:principal] userInfo:nil];
        NSApplication *app=[cls sharedApplication];
        NSURL *resources=[contents URLByAppendingPathComponent:@"Resources" isDirectory:YES], *nibURL=nil;
        NSMutableArray *directories=[NSMutableArray array];
        for (NSString *language in NSBundle.mainBundle.preferredLocalizations) [directories addObject:[resources URLByAppendingPathComponent:[language stringByAppendingString:@".lproj"] isDirectory:YES]];
        [directories addObject:[resources URLByAppendingPathComponent:@"Base.lproj" isDirectory:YES]]; [directories addObject:resources];
        for (NSURL *directory in directories) {
            NSURL *candidate=[directory URLByAppendingPathComponent:[nib stringByAppendingPathExtension:@"nib"]];
            if ([NSFileManager.defaultManager fileExistsAtPath:candidate.path]) { nibURL=candidate; break; }
        }
        if (!nibURL) @throw [NSException exceptionWithName:NSInvalidArgumentException reason:@"Desktop main nib was not found" userInfo:nil];
        NSData *data=[NSData dataWithContentsOfURL:nibURL options:0 error:error]; if (!data) return NO;
        NSArray *top=EXNibInstantiate(data,app,^id(NSString *name,BOOL isOwner,NSError **factoryError) {
            if (isOwner && ![name isEqual:principal]) {
                if (factoryError) *factoryError=[NSError errorWithDomain:@"ExcelPort.Startup" code:3 userInfo:@{NSLocalizedDescriptionKey:@"Nib owner class does not match NSPrincipalClass"}];
                return nil;
            }
            if (isOwner || [name isEqual:@"NSApplication"] || [name isEqual:principal]) return app;
            Class type=NSClassFromString(name); id object=nil;
            if (type==NSFontManager.class) object=[NSFontManager sharedFontManager];
            else if (type && [type isSubclassOfClass:NSDocumentController.class]) object=[type sharedDocumentController];
            else if (type && [name isEqual:@"XLAppDelegate"]) object=[[type alloc] init];
            // A synthetic delegate name is allowed solely in the separate contract-test build.
#ifdef EXCELSHIM_CONTRACT_TEST
            else if (type && [name isEqual:@"EXTestDelegate"]) object=[[type alloc] init];
#endif
            if (!object && factoryError) *factoryError=[NSError errorWithDomain:@"ExcelPort.Startup" code:2 userInfo:@{NSLocalizedDescriptionKey:[@"Unimplemented startup nib class: " stringByAppendingString:name]}];
            return object;
        },error);
        if (!top) return NO; EXTopLevelObjects=top;
        ExcelShimLog(@"Desktop nib instantiated and outlets connected; invoking real delegate callbacks");
        [app finishLaunching]; return YES;
    } @catch (NSException *exception) {
        ExcelShimLog([NSString stringWithFormat:@"Desktop startup failed: %@: %@",exception.name,exception.reason]);
        if (error) *error=[NSError errorWithDomain:@"ExcelPort.Startup" code:1 userInfo:@{NSLocalizedDescriptionKey:exception.reason ?: exception.name}]; return NO;
    }
}

#if TARGET_OS_IOS
@interface EXDesktopScene : UIResponder <UIWindowSceneDelegate>
@property(nonatomic,strong) UIWindow *window;
@end
@implementation EXDesktopScene
- (void)scene:(UIScene *)scene willConnectToSession:(UISceneSession *)session options:(UISceneConnectionOptions *)options {
    self.window=[[UIWindow alloc] initWithWindowScene:(UIWindowScene *)scene];
    self.window.rootViewController=[UIViewController new];
    self.window.rootViewController.view.backgroundColor=UIColor.systemBackgroundColor; [self.window makeKeyAndVisible];
}
- (void)sceneDidBecomeActive:(UIScene *)scene {
    ExcelShimSetApplicationActive(YES); static BOOL started=NO;
    if (started) return;
    started=YES;
    [NSTimer scheduledTimerWithTimeInterval:0.01 repeats:NO block:^(NSTimer *timer) {
        // Excel's entry is just a tail-call to NSApplicationMain. Do not call main again.
        NSURL *contents=[NSBundle.mainBundle.bundleURL URLByAppendingPathComponent:@"Desktop/Microsoft Excel.app/Contents" isDirectory:YES];
        NSError *error=nil;
        if (!ExcelShimStartDesktopApplication(contents,&error)) { ExcelShimLog([@"FIRST STARTUP FAILURE: " stringByAppendingString:error.localizedDescription]); return; }
        ExcelShimSetApplicationActive(YES);
    }];
}
- (void)sceneWillResignActive:(UIScene *)scene {
    ExcelShimSetApplicationActive(NO);
}
@end
@interface EXDesktopUIKitDelegate : UIResponder <UIApplicationDelegate> @end
@implementation EXDesktopUIKitDelegate
- (BOOL)application:(UIApplication *)app didFinishLaunchingWithOptions:(NSDictionary *)options { ExcelShimInitialize(); ExcelShimLog(@"UIKit launched via Excel NSApplicationMain bridge"); return YES; }
- (UISceneConfiguration *)application:(UIApplication *)app configurationForConnectingSceneSession:(UISceneSession *)session options:(UISceneConnectionOptions *)options {
    UISceneConfiguration *configuration=[[UISceneConfiguration alloc] initWithName:@"Excel Desktop" sessionRole:session.role]; configuration.delegateClass=EXDesktopScene.class; return configuration;
}
@end
#endif
int NSApplicationMain(int argc, const char * const *argv) {
    EXRequireMainThread(); ExcelShimInitialize();
#if TARGET_OS_IOS
    static BOOL entered=NO;
    if (entered) @throw [NSException exceptionWithName:NSInternalInconsistencyException reason:@"NSApplicationMain bridge entered twice" userInfo:nil];
    entered=YES;
    return UIApplicationMain(argc,(char **)argv,nil,NSStringFromClass(EXDesktopUIKitDelegate.class));
#else
    @throw [NSException exceptionWithName:NSInternalInconsistencyException reason:@"NSApplicationMain bridge is an iOS entrypoint; use the separate native contract test on macOS" userInfo:nil];
#endif
}
