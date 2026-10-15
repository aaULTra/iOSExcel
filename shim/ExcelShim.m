// Diagnostics infrastructure only. No AppKit compatibility is claimed yet.
#import "ExcelShim.h"
#import <objc/runtime.h>
#include <fcntl.h>
#include <unistd.h>
static int logFD = -1;
static void Uncaught(NSException *exception) {
    ExcelShimLog([NSString stringWithFormat:@"UNCAUGHT %@: %@\n%@", exception.name, exception.reason, exception.callStackSymbols]);
}
void ExcelShimInitialize(void) {
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        NSURL *documents = [NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask].firstObject;
        NSURL *url = [documents URLByAppendingPathComponent:@"excelshim.log"];
        logFD = open(url.fileSystemRepresentation, O_CREAT | O_WRONLY | O_APPEND, 0600);
        NSSetUncaughtExceptionHandler(Uncaught);
        ExcelShimLog(@"ExcelShim diagnostics loaded; AppKit compatibility NOT implemented");
    });
}
void ExcelShimLog(NSString *message) {
    @synchronized (NSFileManager.defaultManager) {
        NSString *line = [NSString stringWithFormat:@"%@ %@\n", NSDate.date.description, message];
        NSData *bytes = [line dataUsingEncoding:NSUTF8StringEncoding];
        if (logFD >= 0) {
            const uint8_t *p = bytes.bytes; NSUInteger left = bytes.length;
            while (left) { ssize_t n = write(logFD, p, left); if (n <= 0) break; p += n; left -= n; }
            fsync(logFD);
        }
        NSLog(@"%@", message);
    }
}
void ExcelShimUnimplemented(id receiver, SEL selector) {
    NSString *message = [NSString stringWithFormat:@"UNIMPLEMENTED %@ %@", NSStringFromClass(object_getClass(receiver)), NSStringFromSelector(selector)];
    ExcelShimLog(message);
    @throw [NSException exceptionWithName:@"ExcelShimUnimplemented" reason:message userInfo:nil];
}
