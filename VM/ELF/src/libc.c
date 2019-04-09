#include "stdio.h"
#include "string.h"

static FILE __stdin = {.fd = STDIN};
static FILE __stdout = {.fd = STDOUT};
static FILE __stderr = {.fd = STDERR};

FILE *stdin = &__stdin;
FILE *stdout = &__stdout;
FILE *stderr = &__stderr;

size_t puts(const char *str) {
    static const char newline = '\n';

    size_t ret = fputs(str, stdout);

    return ret + sys_write(STDOUT, &newline, 1);
}

int getchar(void) {
    static char ret;

    sys_read(STDIN, &ret, 1);

    return ret;
}

char *fgets(char *str, int num, FILE *stream) {
    sys_read(stream->fd, str, num);

    return str;
}

int fputs(const char *str, FILE *stream) {
    return sys_write(stream->fd, str, strlen(str));
}


size_t strlen(const char *str) {
    size_t ret = 0;

    for(; *str; ++str, ++ret)
        ;

    return ret;
}

void *memset(void *ptr, int value, size_t num) {
    /* Fill block of memory.
     * Sets the first `num` bytes of the block of memory pointed by `ptr` to the specified value (interpreted as an unsigned char).
     */

    unsigned char val = (unsigned char)value;
    unsigned char *p = (unsigned char *)ptr;

    while (num--) {
        (*p++) = val;
    }

    return ptr;
}