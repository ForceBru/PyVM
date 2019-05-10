#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define MAXLEN 64

static const char *greeting = "Hello, world!";

int main() {
    char *data = (char *)malloc(MAXLEN);

    if (data == NULL) {
        printf("Failed to allocate %u bytes of memory!\n", MAXLEN);
        return -1;
    }
    memset(data, 0, MAXLEN);
    memcpy(data, greeting, strlen(greeting));

    printf("String: '%s'\n", data);

    free(data);

    return 0;
}