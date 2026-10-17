#ifdef __linux__
#define _GNU_SOURCE
#endif
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

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
        if (strncmp(line, "LIB\t", 4) == 0) {
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
