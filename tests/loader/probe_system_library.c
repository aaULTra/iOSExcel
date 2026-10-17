#ifdef __linux__
#define _GNU_SOURCE
#endif
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#ifdef __APPLE__
#include <mach-o/dyld.h>
#include <mach-o/loader.h>
#endif

static void image_provenance(const char *library) {
#ifdef __APPLE__
    const char *leaf = strrchr(library, '/');
    leaf = leaf ? leaf+1 : library;
    for (uint32_t i=0; i<_dyld_image_count(); ++i) {
        const char *path = _dyld_get_image_name(i);
        const char *name = path ? strrchr(path, '/') : NULL;
        if (!name || strcmp(name+1, leaf) != 0) continue;
        const struct mach_header *header = _dyld_get_image_header(i);
        uint32_t platform = 0;
        if (header && header->magic == MH_MAGIC_64) {
            const struct mach_header_64 *h = (const struct mach_header_64 *)header;
            const unsigned char *cursor = (const unsigned char *)(h+1);
            const unsigned char *end = cursor+h->sizeofcmds;
            for (uint32_t j=0; j<h->ncmds && cursor+sizeof(struct load_command)<=end; ++j) {
                const struct load_command *cmd = (const struct load_command *)cursor;
                if (cmd->cmdsize < sizeof(*cmd) || cmd->cmdsize > (size_t)(end-cursor)) break;
                if (cmd->cmd == LC_BUILD_VERSION && cmd->cmdsize >= sizeof(struct build_version_command))
                    platform = ((const struct build_version_command *)cmd)->platform;
                cursor += cmd->cmdsize;
            }
        }
        printf("IMAGE\t%s\t%u\n", path, platform);
    }
#else
    (void)library;
#endif
}

static int manifest(const char *path) {
    FILE *file = fopen(path, "r");
    if (!file) return 6;
    char line[4096];
    void *handle = NULL;
    int seen = 0;
    while (fgets(line, sizeof(line), file)) {
        size_t size = strlen(line);
        if (!size || line[size-1] != '\n') { fclose(file); return 7; }
        line[size-1] = 0;
        if (strncmp(line, "PREFLIGHT\t", 10) == 0) {
            const char *library = line+10;
            handle = NULL; seen = 1;
            fprintf(stderr, "PROBE_PREFLIGHT %s\n", library); fflush(stderr);
#ifdef __APPLE__
            int compatible = dlopen_preflight(library) ? 1 : 0;
            printf("LIBRARY_PREFLIGHT\t%s\t%d\n", library, compatible);
            if (!compatible) {
                const char *error = dlerror();
                fprintf(stderr, "PROBE_PREFLIGHT_ERROR %s: %s\n", library, error ? error : "No dyld error supplied");
                fflush(stderr);
            }
#else
            printf("LIBRARY_PREFLIGHT\t%s\t-1\n", library);
#endif
        } else if (strncmp(line, "LIB\t", 4) == 0) {
            const char *library = line+4;
            fprintf(stderr, "PROBE_START %s\n", library); fflush(stderr);
            handle = dlopen(library, RTLD_LAZY | RTLD_LOCAL);
            seen = 1;
            if (!handle) {
                printf("LIBRARY_FAILED\t%s\n", library);
                fprintf(stderr, "PROBE_DLOPEN_ERROR %s: %s\n", library, dlerror());
                fflush(stderr);
            }
            else {
                printf("LIBRARY_LOADED\t%s\n", library);
                image_provenance(library);
                fprintf(stderr, "PROBE_DLOPEN_OK %s\n", library); fflush(stderr);
            }
        } else if (strncmp(line, "SYM\t", 4) == 0 && seen) {
            if (!handle) continue;
            const char *name = line+4;
            dlerror();
            void *symbol = dlsym(handle, name);
            const char *error = dlerror();
            if (error || !symbol) printf("MISSING\t%s\n", name);
            else {
                Dl_info info = {0};
                if (!dladdr(symbol, &info) || !info.dli_fname) { fclose(file); return 5; }
                printf("FOUND\t%s\t%s\n", name, info.dli_fname);
            }
        } else { fclose(file); return 8; }
        fflush(stdout);
    }
    int failed = ferror(file);
    fclose(file);
    return failed || !seen ? 9 : 0;
}

int main(int argc, char **argv) {
    if (argc == 3 && strcmp(argv[1], "--manifest") == 0) return manifest(argv[2]);
    if (argc < 3) return 2;
    fprintf(stderr, "PROBE_START %s\n", argv[1]);
    fflush(stderr);
    void *handle = dlopen(argv[1], RTLD_LAZY | RTLD_LOCAL);
    if (!handle) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 3; }
    fprintf(stderr, "PROBE_DLOPEN_OK\n");
    fflush(stderr);
    int audit = strcmp(argv[2], "--audit") == 0;
    for (int i = audit ? 3 : 2; i < argc; ++i) {
        dlerror();
        void *symbol = dlsym(handle, argv[i]);
        const char *error = dlerror();
        if (error || !symbol) {
            printf("MISSING\t%s\n", argv[i]);
            if (!audit) return 4;
            continue;
        }
        Dl_info info = {0};
        if (!dladdr(symbol, &info) || !info.dli_fname) return 5;
        printf("FOUND\t%s\t%s\n", argv[i], info.dli_fname);
    }
    return 0;
}
