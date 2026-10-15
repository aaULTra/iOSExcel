#include <stdio.h>
extern int EXLoaderAppKitValue(void);
extern int EXLoaderCocoaValue(void);
int main(void) {
    int value = EXLoaderAppKitValue() + EXLoaderCocoaValue();
    if (value != 42) return 1;
    puts("PASS: native dyld resolved two original library ordinals through two facades into one shared implementation (42). No Excel code loaded.");
    return 0;
}
