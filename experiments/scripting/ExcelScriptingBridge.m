#import "ExcelScriptingBridge.h"
#import "ExcelShim.h"

static void Unavailable(NSString *operation) {
    ExcelShimLog([NSString stringWithFormat:@"ScriptingBridge %@ unavailable: no Apple-event target, permission, identity or successful operation is fabricated", operation]);
}

@implementation SBObject
- (instancetype)init { Unavailable(@"SBObject init"); return nil; }
- (void)doesNotRecognizeSelector:(SEL)selector { ExcelShimUnimplemented(self, selector); }
+ (void)doesNotRecognizeSelector:(SEL)selector { ExcelShimUnimplemented(self, selector); }
@end

@implementation SBApplication
- (instancetype)init { Unavailable(@"SBApplication init"); return nil; }
+ (instancetype)currentApplication { Unavailable(@"currentApplication"); return nil; }
+ (instancetype)applicationWithBundleIdentifier:(NSString *)identifier {
    (void)identifier;
    Unavailable(@"applicationWithBundleIdentifier:");
    return nil;
}
+ (instancetype)applicationWithProcessIdentifier:(pid_t)identifier {
    (void)identifier;
    Unavailable(@"applicationWithProcessIdentifier:");
    return nil;
}
@end
