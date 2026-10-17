// Experimental forwarding to genuine Apple implementations, not an auth stub.
#import "ExcelKerberos.h"
#import "ExcelShim.h"
#import <GSS/GSS.h>
#import <TargetConditionals.h>
#include <dlfcn.h>
#include <errno.h>
#include <mach-o/loader.h>

// Legacy macOS imports a pointer variable; modern GSS supplies an OID macro.
// Export a real data object containing the actual public GSS descriptor address.
// An asm name avoids redefining the SDK macro or copying its private symbol name.
gss_OID EXDesktopUserNameOID __asm__("_GSS_C_NT_USER_NAME") = GSS_C_NT_USER_NAME;

static int32_t (*nativeInit)(EXKrb5Context *);
static void (*nativeFree)(EXKrb5Context);
static int32_t (*nativeHostRealm)(EXKrb5Context, const char *, char ***);
static int32_t (*nativeFreeRealm)(EXKrb5Context, char *const *);
static NSDictionary *providerReport;

static uint32_t Platform(const void *base) {
    const struct mach_header_64 *h = base;
    if (!h || h->magic != MH_MAGIC_64 || h->cputype != CPU_TYPE_ARM64 || h->sizeofcmds > 1024*1024) return 0;
    const unsigned char *cursor = (const unsigned char *)(h+1), *end = cursor+h->sizeofcmds;
    uint32_t platform = 0;
    for (uint32_t i=0; i<h->ncmds; ++i) {
        if ((size_t)(end-cursor) < sizeof(struct load_command)) return 0;
        const struct load_command *c = (const struct load_command *)cursor;
        if (c->cmdsize < sizeof(*c) || c->cmdsize > (size_t)(end-cursor)) return 0;
        if (c->cmd == LC_BUILD_VERSION && c->cmdsize >= sizeof(struct build_version_command)) {
            if (platform) return 0;
            platform = ((const struct build_version_command *)c)->platform;
        }
        cursor += c->cmdsize;
    }
    return platform;
}

static BOOL Ready(void) {
    static dispatch_once_t once;
    dispatch_once(&once, ^{
#if TARGET_OS_SIMULATOR
        uint32_t expected = 7;
#elif TARGET_OS_OSX
        uint32_t expected = 1;
#else
        uint32_t expected = 2;
#endif
        void *library = dlopen("/System/Library/Frameworks/GSS.framework/GSS", RTLD_LOCAL | RTLD_LAZY);
        const char *names[] = {"krb5_init_context", "krb5_free_context", "krb5_get_host_realm", "krb5_free_host_realm"};
        void *functions[4] = {0};
        NSMutableArray *provenance = [NSMutableArray array];
        BOOL valid = library != NULL;
        const void *commonBase = NULL;
        for (NSUInteger i=0; i<4 && library; ++i) {
            dlerror();
            functions[i] = dlsym(library, names[i]);
            const char *error = dlerror();
            Dl_info info = {0};
            BOOL found = !error && functions[i] && dladdr(functions[i], &info) && info.dli_fname;
            NSString *path = found ? @(info.dli_fname) : @"";
            uint32_t platform = found ? Platform(info.dli_fbase) : 0;
            BOOL systemImage = [path hasPrefix:@"/System/Library/"] ||
                ([path containsString:@".simruntime/Contents/Resources/RuntimeRoot/System/Library/"] && expected == 7);
            if (!found || platform != expected || !systemImage) valid = NO;
            if (i == 0 && found) commonBase = info.dli_fbase;
            if (found && info.dli_fbase != commonBase) valid = NO;
            [provenance addObject:@{@"symbol":@(names[i]), @"provider":path, @"platform":@(platform), @"found":@(found)}];
        }
        if (valid) {
            nativeInit = (int32_t (*)(EXKrb5Context *))functions[0];
            nativeFree = (void (*)(EXKrb5Context))functions[1];
            nativeHostRealm = (int32_t (*)(EXKrb5Context, const char *, char ***))functions[2];
            nativeFreeRealm = (int32_t (*)(EXKrb5Context, char *const *))functions[3];
        }
        // Keep the dlopen reference alive for the lifetime of all opaque contexts.
        providerReport = @{@"ready":@(valid), @"expected_platform":@(expected), @"functions":provenance,
            @"scope":@"Private Apple implementation reached through public GSS; version-sensitive experimental ABI. No authentication or activation success implied."};
        ExcelShimLog([@"Kerberos provider audit: " stringByAppendingString:providerReport.description]);
    });
    return [providerReport[@"ready"] boolValue];
}

NSDictionary *ExcelKerberosProviderReport(void) { Ready(); return providerReport; }

int32_t krb5_init_context(EXKrb5Context *context) {
    ExcelShimLog(@"Kerberos krb5_init_context: forwarding genuine provider or returning an error");
    if (!context) return EINVAL;
    *context = NULL;
    return Ready() ? nativeInit(context) : ENOSYS;
}

void krb5_free_context(EXKrb5Context context) {
    ExcelShimLog(@"Kerberos krb5_free_context");
    if (!context) return;
    if (!Ready()) @throw [NSException exceptionWithName:@"ExcelShimUnavailableProvider" reason:@"Cannot free a Kerberos context without its original provider" userInfo:nil];
    nativeFree(context);
}

int32_t krb5_get_host_realm(EXKrb5Context context, const char *host, char ***realms) {
    ExcelShimLog(@"Kerberos krb5_get_host_realm: forwarding without fabricating realm data");
    if (!realms || !context) return EINVAL;
    *realms = NULL;
    return Ready() ? nativeHostRealm(context, host, realms) : ENOSYS;
}

int32_t krb5_free_host_realm(EXKrb5Context context, char *const *realms) {
    ExcelShimLog(@"Kerberos krb5_free_host_realm");
    if (!context) return EINVAL;
    return Ready() ? nativeFreeRealm(context, realms) : ENOSYS;
}
