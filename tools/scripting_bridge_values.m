// Interface/ABI metadata only. Do not instantiate targets or send Apple events.
#import <Foundation/Foundation.h>
#import <ScriptingBridge/ScriptingBridge.h>
#import <objc/runtime.h>

int main(int argc, char **argv) { @autoreleasepool {
    if (argc != 2) return 2;
    NSMutableArray *classes = [NSMutableArray array];
    for (Class cls in @[[SBObject class], [SBApplication class]]) {
        NSMutableArray *methods = [NSMutableArray array];
        for (int meta=0; meta<2; ++meta) {
            unsigned count = 0;
            Method *list = class_copyMethodList(meta ? object_getClass(cls) : cls, &count);
            for (unsigned i=0; i<count; ++i) {
                [methods addObject:@{@"selector":NSStringFromSelector(method_getName(list[i])),
                    @"encoding":@(method_getTypeEncoding(list[i])), @"class_method":@(meta != 0)}];
            }
            free(list);
        }
        [classes addObject:@{@"name":NSStringFromClass(cls), @"superclass":NSStringFromClass(class_getSuperclass(cls)), @"methods":methods}];
    }
    NSDictionary *report = @{@"classes":classes, @"scope":@"Actual native Mac method encodings. No targets instantiated, no Apple events, authentication or Office code executed."};
    NSData *data = [NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:NULL];
    return [data writeToFile:@(argv[1]) atomically:YES] ? 0 : 3;
} }
