#include "syscalls.h"

int main(void);

__attribute__((noreturn)) void _start(void) {
    sys_exit(main());
}