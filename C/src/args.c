#include <stdio.h>
#include <string.h>

size_t my_strlen(char *str) {
    size_t ret = 0;
    for (unsigned i = 0; str[i] != 0; ++i, ++ret) {
        printf("i=%d str[i]=%d\n", i, str[i]);
    }

    return ret;
}

int main(int argc, char **argv) {
    printf("Got %d arguments\n", argc);

    for (; argc >= 0; --argc) {
        printf("Argument %d: '%s' (addr=0x%08x)\n", argc, argv[argc], *(argv + argc));
    }

    return 0;
}
