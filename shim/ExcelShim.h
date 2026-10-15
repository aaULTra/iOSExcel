#import <Foundation/Foundation.h>
FOUNDATION_EXPORT void ExcelShimInitialize(void);
FOUNDATION_EXPORT void ExcelShimLog(NSString *message);
FOUNDATION_EXPORT void ExcelShimUnimplemented(id receiver, SEL selector) __attribute__((noreturn));
