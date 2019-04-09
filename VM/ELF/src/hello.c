#include "syscalls.h"

size_t strlen(const char *str) {
    size_t ret = 0;

    for(; *str; ++str, ++ret)
        ;

    return ret;
}

size_t puts(const char *str) {
    static const char newline = '\n';

    size_t ret = sys_write(STDOUT, str, strlen(str));
    return ret + sys_write(STDOUT, &newline, 1);
}

int getchar(void) {
    static char ret;

    sys_read(STDIN, &ret, 1);

    return ret;
}

char *fgets(char *str, int num, int stream) {
    sys_read(stream, str, num);

    return str;
}

int fputs(const char *str, int stream) {
    return sys_write(stream, str, strlen(str));
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

#define MAX_INPUT 255

const char *data = "Hello, world!";
const char *input_prompt = "Input something: ";
const char *output_prompt = "You entered: ";
int main(void) {
    char input[MAX_INPUT] = {0};

    puts(data);

    fputs(input_prompt, STDOUT);
    fgets(input, MAX_INPUT, STDIN);

    fputs(output_prompt, STDOUT);

    return fputs(input, STDOUT);
}