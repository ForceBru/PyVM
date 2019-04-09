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

    sys_write(STDOUT, input_prompt, strlen(input_prompt));
    size_t len_read = sys_read(STDIN, input, MAX_INPUT);

    input[len_read - 1] = 0;  // get rid of newline!

    sys_write(STDOUT, output_prompt, strlen(output_prompt));

    return puts(input);
}