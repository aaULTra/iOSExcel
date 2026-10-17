#import <Foundation/Foundation.h>
#include <stddef.h>
#ifdef EX_KERBEROS_BASELINE
#import <Kerberos/Kerberos.h>
#import "ExcelKerberos.h"
// Importing the measured Mac declarations alongside our declarations makes
// any incompatible function signature a compiler error.
_Static_assert(sizeof(krb5_error_code)==4, "krb5_error_code width");
#else
#import <GSS/GSS.h>
#import "ExcelKerberos.h"
#include <dlfcn.h>
#endif

int main(int argc, char **argv) { @autoreleasepool {
    if (argc != 2) return 2;
    gss_OID oid;
#ifdef EX_KERBEROS_BASELINE
    oid = GSS_C_NT_USER_NAME;
#else
    void *symbol = dlsym(RTLD_DEFAULT, "GSS_C_NT_USER_NAME");
    if (!symbol) return 3;
    oid = *(gss_OID *)symbol;
    if (oid != GSS_C_NT_USER_NAME) return 4;
    if (![ExcelKerberosProviderReport()[@"ready"] boolValue]) return 5;
#endif
    if (!oid || !oid->elements || oid->length > 128) return 6;
    NSData *bytes = [NSData dataWithBytes:oid->elements length:oid->length];
    EXKrb5Context context = NULL;
    int32_t initialized = krb5_init_context(&context);
    if (initialized || !context) return 7;
    char **realms = NULL;
    int32_t lookup = krb5_get_host_realm(context, "localhost", &realms);
    BOOL supplied = realms != NULL;
    int32_t freed = supplied ? krb5_free_host_realm(context, realms) : 0;
    krb5_free_context(context);
    if (freed) return 8;
    NSDictionary *report = @{@"oid_base64":[bytes base64EncodedStringWithOptions:0],
        @"oid_length":@(oid->length), @"oid_struct_size":@(sizeof(*oid)),
        @"oid_elements_offset":@(offsetof(gss_OID_desc, elements)),
        @"context_allocated_and_freed":@YES, @"realm_lookup_status":@(lookup),
        @"realm_list_returned":@(supplied), @"returned_realm_list_freed":@(supplied),
        @"credentials_used":@NO, @"authentication_attempted":@NO, @"excel_executed":@NO};
#ifndef EX_KERBEROS_BASELINE
    NSMutableDictionary *combined = [report mutableCopy];
    combined[@"provider"] = ExcelKerberosProviderReport();
    report = combined;
#endif
    NSData *data = [NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:NULL];
    return [data writeToFile:@(argv[1]) atomically:YES] ? 0 : 9;
} }
