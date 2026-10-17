#pragma once
#import <Foundation/Foundation.h>
#include <stdint.h>
// Exact legacy Mac signatures captured from MacOSX15.5 Kerberos headers.
// Contexts remain opaque and are always allocated/freed by Apple's provider.
typedef struct _krb5_context *EXKrb5Context;
int32_t krb5_init_context(EXKrb5Context *context);
void krb5_free_context(EXKrb5Context context);
int32_t krb5_get_host_realm(EXKrb5Context context, const char *host, char ***realms);
int32_t krb5_free_host_realm(EXKrb5Context context, char *const *realms);
FOUNDATION_EXPORT NSDictionary *ExcelKerberosProviderReport(void);
