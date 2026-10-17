#import <Foundation/Foundation.h>
#import <ApplicationServices/ApplicationServices.h>

int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 2) return 2;
#define EXType(T) @#T: [NSString stringWithUTF8String:@encode(T)]
        NSDictionary *report = @{
            @"scope": @"Actual arm64 Mac SDK types and public constant values; no Office or clipboard operations",
            @"types": @{EXType(Boolean), EXType(OSStatus), EXType(ItemCount), EXType(PMOrientation),
                EXType(PMDestinationType), EXType(PMRect), EXType(PMResolution), EXType(PMObject),
                EXType(PMPrinter), EXType(PMPageFormat), EXType(PMPrintSession), EXType(PMPrintSettings),
                EXType(PasteboardItemID), EXType(PasteboardSyncFlags), EXType(PasteboardFlavorFlags),
                EXType(HIShapeRef), EXType(UAZoomChangeFocusType)},
            @"constants": @{@"kPMNotImplemented": @(kPMNotImplemented), @"unimpErr": @(unimpErr),
                @"paramErr": @(paramErr), @"kPasteboardModified": @(kPasteboardModified),
                @"kPasteboardClientIsOwner": @(kPasteboardClientIsOwner)},
            @"names": @{@"kPasteboardClipboard": (__bridge NSString *)kPasteboardClipboard,
                @"kPasteboardFind": (__bridge NSString *)kPasteboardFind}
        };
        NSError *error = nil;
        NSData *data = [NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:&error];
        if (!data || ![data writeToFile:[NSString stringWithUTF8String:argv[1]] options:NSDataWritingAtomic error:&error]) {
            NSLog(@"%@", error); return 3;
        }
        return 0;
    }
}
