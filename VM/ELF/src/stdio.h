#include "syscalls.h"

#ifndef STDIO_H
#define STDIO_H

typedef struct {
    unsigned int fd;
} FILE;

FILE *stdin;
FILE *stdout;
FILE *stderr;

size_t puts(const char *str);
int getchar(void);
char *fgets(char *str, int num, FILE *stream);
int fputs(const char *str, FILE *stream);

#endif