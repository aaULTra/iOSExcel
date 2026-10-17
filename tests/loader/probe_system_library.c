#include <dlfcn.h>
#include <stdio.h>

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    void *handle = dlopen(argv[1], RTLD_LAZY | RTLD_LOCAL);
    if (!handle) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 3; }
    void *symbol = dlsym(handle, argv[2]);
    if (!symbol) { fprintf(stderr, "dlsym: %s\n", dlerror()); return 4; }
    Dl_info info = {0};
    if (!dladdr(symbol, &info) || !info.dli_fname) return 5;
    printf("Loaded %s; resolved %s from %s. No API invoked.\n", argv[1], argv[2], info.dli_fname);
    return 0;
}
