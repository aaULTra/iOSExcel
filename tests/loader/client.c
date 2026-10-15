#include <stdio.h>
extern int EXLoaderAppKitValue(void);
extern int EXLoaderCocoaValue(void);
int main(void) {
    int value = EXLoaderAppKitValue() + EXLoaderCocoaValue();
    if (value != 42) return 1;
    puts("PASS: native fixture returned 42. No Excel code loaded.");
    return 0;
}
