#import "ExcelSecurityInterface.h"
#import "ExcelShim.h"

@implementation NSWindow
+ (instancetype)allocWithZone:(NSZone *)zone {
    (void)zone;
    ExcelShimLog(@"Window allocation unavailable; no desktop window or security dialog created");
    ExcelShimUnimplemented(self, _cmd);
}
+ (void)doesNotRecognizeSelector:(SEL)selector { ExcelShimUnimplemented(self, selector); }
- (void)doesNotRecognizeSelector:(SEL)selector { ExcelShimUnimplemented(self, selector); }
@end
@implementation NSPanel
@end
@implementation SFCertificatePanel
+ (instancetype)sharedCertificatePanel { ExcelShimUnimplemented(self, _cmd); }
@end
@implementation SFCertificateTrustPanel
+ (instancetype)sharedCertificateTrustPanel { ExcelShimUnimplemented(self, _cmd); }
@end
@implementation SFChooseIdentityPanel
+ (instancetype)sharedChooseIdentityPanel { ExcelShimUnimplemented(self, _cmd); }
@end
