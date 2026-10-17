// Metadata/value capture only. Do not enumerate launchd jobs or invoke helpers.
#import <Foundation/Foundation.h>
#import <ServiceManagement/ServiceManagement.h>
int main(int argc, char **argv) { @autoreleasepool {
    if (argc != 2 || !kSMDomainUserLaunchd || CFGetTypeID(kSMDomainUserLaunchd)!=CFStringGetTypeID()) return 2;
    CFArrayRef (*contract)(CFStringRef) = SMCopyAllJobDictionaries;
    if (!contract) return 3;
    NSDictionary *report=@{@"user_domain":(__bridge NSString *)kSMDomainUserLaunchd,
        @"domain_declaration_encoding":@(@encode(__typeof__(kSMDomainUserLaunchd))),
        @"function_pointer_encoding":@(@encode(__typeof__(contract))),
        @"domain_pointer_bytes":@(sizeof(kSMDomainUserLaunchd)),
        @"jobs_enumerated":@NO,@"helpers_invoked":@NO,@"authentication_attempted":@NO,@"excel_executed":@NO};
    NSData *data=[NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:NULL];
    return [data writeToFile:@(argv[1]) atomically:YES] ? 0 : 4;
} }
