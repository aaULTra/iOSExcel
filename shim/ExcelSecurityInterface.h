#import "ExcelAppKit.h"
// Diagnostic class hierarchy only. Allocation and dialog access always raise.
// No window, certificate UI, trust setting or identity selection is implemented.
@interface NSWindow : NSResponder
@end
@interface NSPanel : NSWindow
@end
@interface SFCertificatePanel : NSPanel
+ (instancetype)sharedCertificatePanel;
@end
@interface SFCertificateTrustPanel : SFCertificatePanel
+ (instancetype)sharedCertificateTrustPanel;
@end
@interface SFChooseIdentityPanel : NSPanel
+ (instancetype)sharedChooseIdentityPanel;
@end
