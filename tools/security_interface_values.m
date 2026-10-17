// Native baseline reads class metadata only: no security panels or trust APIs run.
#import <Foundation/Foundation.h>
#ifdef EXCELSHIM_SECURITY_CONTRACT
#import "ExcelSecurityInterface.h"
#else
#import <SecurityInterface/SecurityInterface.h>
#endif
#import <objc/runtime.h>

#ifdef EXCELSHIM_SECURITY_CONTRACT
static BOOL Stops(void (^operation)(void)) {
    @try { operation(); }
    @catch (NSException *exception) {
        return [exception.name isEqualToString:@"ExcelShimUnimplemented"];
    }
    return NO;
}
#endif

int main(int argc, char **argv) { @autoreleasepool {
    if (argc != 2) return 2;
    NSArray *types = @[[NSWindow class], [NSPanel class], [SFCertificatePanel class],
                       [SFCertificateTrustPanel class], [SFChooseIdentityPanel class]];
#ifdef EXCELSHIM_SECURITY_CONTRACT
    if (!Stops(^{ (void)[SFCertificatePanel sharedCertificatePanel]; }) ||
        !Stops(^{ (void)[SFCertificateTrustPanel sharedCertificateTrustPanel]; }) ||
        !Stops(^{ (void)[SFChooseIdentityPanel sharedChooseIdentityPanel]; })) return 4;
    for (Class cls in types) {
        if (objc_lookUpClass(class_getName(cls)) != cls) return 5;
        if (!Stops(^{ (void)[cls alloc]; }) || !Stops(^{ (void)[cls new]; }) ||
            !Stops(^{ (void)[cls allocWithZone:NULL]; })) return 6;
    }
#endif
    NSMutableArray *classes = [NSMutableArray array];
    for (Class cls in types) {
        NSMutableArray *methods = [NSMutableArray array];
        for (NSString *name in @[@"sharedCertificatePanel", @"sharedCertificateTrustPanel", @"sharedChooseIdentityPanel", @"allocWithZone:"]) {
            Method method = class_getClassMethod(cls, NSSelectorFromString(name));
            if (method) [methods addObject:@{@"selector":name, @"encoding":@(method_getTypeEncoding(method))}];
        }
        [classes addObject:@{@"name":NSStringFromClass(cls), @"superclass":NSStringFromClass(class_getSuperclass(cls)), @"class_methods":methods}];
    }
    NSDictionary *report = @{@"classes":classes, @"excel_executed":@NO,
        @"scope":@"Class hierarchy/method ABI only. No trust evaluation, trust changes, identity, authentication or Microsoft operation performed."};
    NSData *data = [NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:NULL];
    return [data writeToFile:@(argv[1]) atomically:YES] ? 0 : 3;
} }
