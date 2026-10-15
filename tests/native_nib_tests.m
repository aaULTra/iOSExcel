#import <Foundation/Foundation.h>
#import "ExcelNibArchive.h"
#import "ExcelAppKit.h"
static NSMutableArray *Events;
static void Check(BOOL condition, NSString *message) { if (!condition) @throw [NSException exceptionWithName:@"EXTestFailure" reason:message userInfo:nil]; }
@interface EXTestApplication : NSApplication @end
@implementation EXTestApplication
- (void)awakeFromNib { Check(self.delegate!=nil,@"Outlet must be connected before awakeFromNib"); [Events addObject:@"awake-owner"]; }
@end
@interface EXTestDelegate : NSObject @end
@implementation EXTestDelegate
- (void)awakeFromNib { [Events addObject:@"awake-delegate"]; }
- (void)applicationWillFinishLaunching:(NSNotification *)notification { [Events addObject:@"will"]; }
- (void)applicationDidFinishLaunching:(NSNotification *)notification { [Events addObject:@"did"]; }
@end
@interface EXTestDocumentController : NSDocumentController @end
@implementation EXTestDocumentController @end

static EXNibObjectFactory Factory(id owner) {
    return ^id(NSString *name,BOOL isOwner,NSError **error) {
        if (isOwner || [name isEqual:@"NSApplication"]) return owner;
        if ([name isEqual:@"EXTestDelegate"] || [name isEqual:@"XLAppDelegate"]) return [EXTestDelegate new];
        if ([name isEqual:@"EXTestDocumentController"] || [name isEqual:@"XLDocumentController"]) return [EXTestDocumentController new];
        if ([name isEqual:@"NSFontManager"]) return [NSFontManager sharedFontManager];
        if (error) *error=[NSError errorWithDomain:@"EXTest" code:1 userInfo:@{NSLocalizedDescriptionKey:[@"No test factory for " stringByAppendingString:name]}]; return nil;
    };
}
int main(int argc,const char **argv) {
    @autoreleasepool { @try {
        Check(argc>=2,@"Synthetic desktop Contents directory required");
        NSURL *contents=[NSURL fileURLWithPath:@(argv[1]) isDirectory:YES];
        NSData *data=[NSData dataWithContentsOfURL:[contents URLByAppendingPathComponent:@"Resources/Base.lproj/Main.nib"]];
        NSError *error=nil; NSDictionary *parsed=EXNibParse(data,&error); Check(parsed!=nil,error.localizedDescription); Check([parsed[@"objects"] count]==18,@"Expected synthetic graph");
        Events=[NSMutableArray array]; EXTestApplication *owner=[EXTestApplication new];
        NSArray *top=EXNibInstantiate(data,owner,Factory(owner),&error);
        Check(top!=nil,error.localizedDescription); Check(top.count==3,@"Owner placeholder must not become a duplicate top-level object"); Check([owner.delegate isKindOfClass:EXTestDelegate.class],@"Delegate outlet must resolve to its instantiated object");
        Check([Events containsObject:@"awake-owner"] && [Events containsObject:@"awake-delegate"],@"awakeFromNib delivery missing");
        for (NSUInteger n=0;n<data.length;n++) { NSError *failure=nil; Check(EXNibParse([data subdataWithRange:NSMakeRange(0,n)],&failure)==nil,@"Truncated archive unexpectedly accepted"); Check(failure!=nil,@"Truncated archive needs a specific error"); }
        NSError *failure=nil; Check(EXNibInstantiate(data,owner,^id(NSString *name,BOOL isOwner,NSError **e){ return isOwner?owner:nil; },&failure)==nil,@"Unimplemented classes must fail"); Check(failure!=nil,@"Missing class failure must be visible");
        if (argc>=3) {
            NSData *real=[NSData dataWithContentsOfFile:@(argv[2])]; NSDictionary *model=EXNibParse(real,&error);
            Check(model!=nil,error.localizedDescription); Check([model[@"objects"] count]==33,@"Actual Excel main-nib structure changed");
            EXTestApplication *standIn=[EXTestApplication new];
            Check(EXNibInstantiate(real,standIn,Factory(standIn),&error)!=nil,error.localizedDescription);
            Check([standIn.delegate isKindOfClass:EXTestDelegate.class],@"Actual archive delegate wiring failed");
            puts("Original Excel startup nib decoded with explicit TEST stand-ins; Excel executable was NOT loaded.");
        }
        [Events removeAllObjects]; Check(ExcelShimStartDesktopApplication(contents,&error),error.localizedDescription);
        Check(NSApp!=nil && NSApp.isRunning,@"Application should be running after startup callbacks");
        NSUInteger will=[Events indexOfObject:@"will"], did=[Events indexOfObject:@"did"];
        Check(will!=NSNotFound && did!=NSNotFound && will<did,@"Launch delegate callback order incorrect");
        [NSApp finishLaunching]; Check([[Events filteredArrayUsingPredicate:[NSPredicate predicateWithFormat:@"SELF == 'did'"]] count]==1,@"Finish-launch callbacks must not run twice");
        puts("PASS: native nib bounds checks, reference identity, delegate outlet, awake ordering, startup callbacks and idempotence. No Excel execution or workbook milestone claimed."); return 0;
    } @catch(NSException *exception) { fprintf(stderr,"FAIL: %s: %s\n",exception.name.UTF8String,exception.reason.UTF8String); return 1; } }
}
