// Read-only type/selector metadata from the runner's real AppKit. No Office code executes.
#import <AppKit/AppKit.h>
#import <objc/runtime.h>
static NSArray *Methods(Class cls) {
    unsigned int count=0; Method *methods=class_copyMethodList(cls,&count); NSMutableArray *out=[NSMutableArray array];
    for (unsigned int i=0;i<count;i++) {
        const char *type=method_getTypeEncoding(methods[i]);
        [out addObject:@{@"selector":NSStringFromSelector(method_getName(methods[i])),@"encoding":type?@(type):@""}];
    }
    free(methods); return [out sortedArrayUsingComparator:^NSComparisonResult(NSDictionary *a,NSDictionary *b){return [a[@"selector"] compare:b[@"selector"]];}];
}
int main(int argc,const char **argv) {
    @autoreleasepool {
        if (argc!=3) { fprintf(stderr,"usage: appkit-contracts class-list.json output.json\n"); return 2; }
        NSError *error=nil; NSData *input=[NSData dataWithContentsOfFile:@(argv[1])];
        NSArray *names=[NSJSONSerialization JSONObjectWithData:input options:0 error:&error];
        if (![names isKindOfClass:NSArray.class]) { fprintf(stderr,"invalid class list\n"); return 2; }
        NSMutableArray *classes=[NSMutableArray array];
        for (NSString *name in names) {
            if (![name isKindOfClass:NSString.class]) return 2;
            Class cls=NSClassFromString(name);
            if (!cls) { [classes addObject:@{@"name":name,@"available":@NO}]; continue; }
            Class superClass=class_getSuperclass(cls); NSMutableArray *ivars=[NSMutableArray array]; unsigned int count=0; Ivar *list=class_copyIvarList(cls,&count);
            for (unsigned int i=0;i<count;i++) {
                const char *n=ivar_getName(list[i]), *t=ivar_getTypeEncoding(list[i]);
                [ivars addObject:@{@"name":n?@(n):@"",@"encoding":t?@(t):@"",@"offset":@(ivar_getOffset(list[i]))}];
            }
            free(list);
            [classes addObject:@{@"name":name,@"available":@YES,@"superclass":superClass?NSStringFromClass(superClass):NSNull.null,@"instance_size":@(class_getInstanceSize(cls)),@"instance_methods":Methods(cls),@"class_methods":Methods(object_getClass(cls)),@"ivars":ivars}];
        }
        NSDictionary *result=@{@"kind":@"macOS AppKit runtime metadata; not iPad ABI or selector availability",@"os":NSProcessInfo.processInfo.operatingSystemVersionString,@"classes":classes};
        NSData *output=[NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:&error];
        if (!output || ![output writeToFile:@(argv[2]) options:NSDataWritingAtomic error:&error]) { fprintf(stderr,"%s\n",error.localizedDescription.UTF8String); return 1; }
        printf("Captured real AppKit contracts for %lu requested classes.\n",(unsigned long)classes.count); return 0;
    }
}
