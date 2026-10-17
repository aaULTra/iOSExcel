#define EXCELSHIM_SERVICE_TYPES_ONLY 1
#import <Foundation/Foundation.h>
#import "ExcelApplicationServices.h"
int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 2) return 2;
#define EXType(T) @#T: [NSString stringWithUTF8String:@encode(T)]
        NSDictionary *actual=@{EXType(Boolean), EXType(OSStatus),
            @"ItemCount":[NSString stringWithUTF8String:@encode(EXDesktopItemCount)],
            EXType(PMOrientation), EXType(PMDestinationType), EXType(PMRect), EXType(PMResolution),
            EXType(PMObject), EXType(PMPrinter), EXType(PMPageFormat), EXType(PMPrintSession),
            EXType(PMPrintSettings), EXType(PasteboardItemID), EXType(PasteboardSyncFlags),
            EXType(PasteboardFlavorFlags), EXType(HIShapeRef), EXType(UAZoomChangeFocusType)};
        NSData *data=[NSData dataWithContentsOfFile:[NSString stringWithUTF8String:argv[1]]];
        NSDictionary *expected=[NSJSONSerialization JSONObjectWithData:data options:0 error:NULL];
        if (![actual isEqual:expected[@"types"]]) { NSLog(@"ABI TYPE MISMATCH: actual=%@ expected=%@",actual,expected[@"types"]); return 3; }
        if ([expected[@"constants"][@"kPMNotImplemented"] intValue]!=EXPrintNotImplemented ||
            [expected[@"constants"][@"unimpErr"] intValue]!=EXServiceNotImplemented) return 4;
        puts("PASS: all 17 compatibility C type encodings and explicit unsupported status values match measured arm64 Mac contracts");
        return 0;
    }
}
