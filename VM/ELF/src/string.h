#ifndef STRING_H
#define STRING_H

#include "syscalls.h"

size_t strlen(const char *str);
void *memset(void *ptr, int value, size_t num);

#endif