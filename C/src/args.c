#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    printf("Got %d arguments\n", argc);

    for (int i = 0; i < argc; ++i) {
        printf("Argument %d: '%s' (addr=0x%08x)\n", i, argv[i], *(argv + i));
    }

    printf("USER='%s'\n", getenv("USER"));

    return 0;
}
