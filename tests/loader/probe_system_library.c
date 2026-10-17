#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
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
