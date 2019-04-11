#ifndef STRING_H
#define STRING_H

#include "syscalls.h"

size_t strlen(const char *str);
void *memset(void *ptr, int value, size_t num);
void *memcpy(void *destination, const void *source, size_t num);
char *strcpy(char * destination, const char *source);
char *strdup(const char *str);

#endif