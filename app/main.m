// Standalone UIKit lifecycle probe. Does NOT load or run Microsoft Excel.
#import <UIKit/UIKit.h>
#import "ExcelShim.h"
@interface ProbeScene : UIResponder <UIWindowSceneDelegate>
@property(nonatomic,strong) UIWindow *window;
@property(nonatomic,strong) NSTimer *heartbeat;
@end
@implementation ProbeScene
- (void)scene:(UIScene *)scene willConnectToSession:(UISceneSession *)session options:(UISceneConnectionOptions *)options {
    self.window = [[UIWindow alloc] initWithWindowScene:(UIWindowScene *)scene];
    UIViewController *vc = [UIViewController new]; vc.view.backgroundColor = UIColor.systemBackgroundColor;
    UILabel *label = [UILabel new]; label.numberOfLines = 0; label.textAlignment = NSTextAlignmentCenter;
    label.text = @"ExcelPort lifecycle probe\n\nUIKit and diagnostic shim only.\nMicrosoft Excel is not loaded.\n\nLog: Files → ExcelPort Probe → excelshim.log";
    label.translatesAutoresizingMaskIntoConstraints = NO; [vc.view addSubview:label];
    [NSLayoutConstraint activateConstraints:@[[label.centerXAnchor constraintEqualToAnchor:vc.view.centerXAnchor], [label.centerYAnchor constraintEqualToAnchor:vc.view.centerYAnchor], [label.widthAnchor constraintLessThanOrEqualToAnchor:vc.view.widthAnchor multiplier:0.85]]];
    self.window.rootViewController = vc; [self.window makeKeyAndVisible];
    ExcelShimLog(@"PROBE window visible; Excel milestone M3 remains untested");
}
- (void)sceneDidBecomeActive:(UIScene *)scene {
    ExcelShimLog(@"PROBE foreground active");
    self.heartbeat = [NSTimer scheduledTimerWithTimeInterval:10 repeats:YES block:^(NSTimer *timer) { ExcelShimLog(@"PROBE foreground heartbeat"); }];
}
- (void)sceneWillResignActive:(UIScene *)scene { [self.heartbeat invalidate]; self.heartbeat = nil; ExcelShimLog(@"PROBE inactive"); }
- (void)sceneDidEnterBackground:(UIScene *)scene { ExcelShimLog(@"PROBE background"); }
@end
@interface ProbeDelegate : UIResponder <UIApplicationDelegate> @end
@implementation ProbeDelegate
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)options { ExcelShimInitialize(); ExcelShimLog(@"PROBE UIKit didFinishLaunching"); return YES; }
- (UISceneConfiguration *)application:(UIApplication *)application configurationForConnectingSceneSession:(UISceneSession *)session options:(UISceneConnectionOptions *)options {
    UISceneConfiguration *config = [[UISceneConfiguration alloc] initWithName:@"Probe" sessionRole:session.role]; config.delegateClass = ProbeScene.class; return config;
}
@end
int main(int argc, char **argv) { @autoreleasepool { ExcelShimInitialize(); ExcelShimLog(@"PROBE main entered"); return UIApplicationMain(argc, argv, nil, NSStringFromClass(ProbeDelegate.class)); } }
