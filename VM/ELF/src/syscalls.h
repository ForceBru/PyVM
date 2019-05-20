#ifndef SYSCALLS_H
#define SYSCALLS_H

#include "stddef.h"

#define __NR_sys_py_dbg  0x00

#define __NR_sys_exit  0x01
#define __NR_sys_read  0x03
#define __NR_sys_write 0x04
#define __NR_sys_brk 0x2d

#define STDIN 0
#define STDOUT 1
#define STDERR 2

#define SYSCALL0(type, name)\
    type name(void) {\
        type ret;\
        __asm__ __volatile__ (\
            "int $0x80"\
            : "=a" (ret)\
            : "0" ((long)__NR_##name)\
        );\
        return ret;\
    }

#define SYSCALL1(type, name, type1, arg1)\
    type name(type1 arg1) {\
        type ret;\
        __asm__ __volatile__ (\
            "int $0x80"\
            : "=a" (ret)\
            : "0" ((long)__NR_##name),\
              "b" ((long)arg1)\
        );\
        return ret;\
    }

#define SYSCALL2(type, name, type1, arg1, type2, arg2)\
    type name(type1 arg1, type2 arg2) {\
        type ret;\
        __asm__ __volatile__ (\
            "int $0x80"\
            : "=a" (ret)\
            : "0" ((long)__NR_##name),\
              "b" ((long)arg1),\
              "c" ((long)arg2)\
        );\
        return ret;\
    }

#define SYSCALL3(type, name, type1, arg1, type2, arg2, type3, arg3)\
    type name(type1 arg1, type2 arg2, type3 arg3) {\
        type ret;\
        __asm__ __volatile__(\
            "int $0x80"\
            : "=a" (ret)\
            : "0" ((long)__NR_##name),\
              "b" ((long)arg1),\
              "c" ((long)arg2),\
              "d" ((long)arg3)\
        );\
        return ret;\
    }

__attribute__((noreturn)) void sys_exit(int code);
size_t sys_read(unsigned int fd, char * buf, size_t count);
size_t sys_write(unsigned int fd, const char * buf, size_t count);
unsigned long sys_brk(unsigned long addr);
void *sbrk(long increment);

size_t sys_py_dbg(const void *data, unsigned type);
size_t py_dbg_string(const char *data);
size_t py_dbg_int(const long data);
size_t py_dbg_uint(const size_t data);

#endif