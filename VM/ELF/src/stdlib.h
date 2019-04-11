#ifndef STDLIB_H
#define STDLIB_H

#include "stddef.h"

void *malloc(size_t size);
void free(void *data);
void *calloc(size_t num, size_t size);

#endif