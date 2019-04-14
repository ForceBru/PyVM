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
SYSCALL1(unsigned long, sys_brk, unsigned long, addr)

SYSCALL2(size_t, sys_py_dbg, const void *, data, unsigned, type)

#undef SYSCALL0
#undef SYSCALL1
#undef SYSCALL2
#undef SYSCALL3

size_t py_dbg_string(const char *data) {
    return sys_py_dbg(data, 0);
}

size_t py_dbg_int(const long data) {
    return sys_py_dbg((void *)data, 2);
}

size_t py_dbg_uint(const size_t data) {
    return sys_py_dbg((void *)data, 1);
}