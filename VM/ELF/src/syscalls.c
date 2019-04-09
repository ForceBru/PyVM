#include "syscalls.h"

void sys_exit(int code) {
    __asm__ volatile (
        "int $0x80"
        :
        : "a" ((long)__NR_sys_exit),
          "b" ((long)code)\
    );
}

SYSCALL3(size_t, sys_read, unsigned int, fd, char *, buf, size_t, count)
SYSCALL3(size_t, sys_write, unsigned int, fd, const char *, buf, size_t, count)

#undef SYSCALL0
#undef SYSCALL1
#undef SYSCALL2
#undef SYSCALL3