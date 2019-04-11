#include "stdio.h"
#include "string.h"
#include "stdlib.h"
#include "stddef.h"

#define FREE_THRESHOLD 512

static FILE __stdin = {.fd = STDIN};
static FILE __stdout = {.fd = STDOUT};
static FILE __stderr = {.fd = STDERR};

FILE *stdin = &__stdin;
FILE *stdout = &__stdout;
FILE *stderr = &__stderr;

size_t puts(const char *str) {
    static const char newline = '\n';

    size_t ret = fputs(str, stdout);

    return ret + sys_write(STDOUT, &newline, 1);
}

int getchar(void) {
    static char ret;

    sys_read(STDIN, &ret, 1);

    return ret;
}

char *fgets(char *str, int num, FILE *stream) {
    sys_read(stream->fd, str, num);

    return str;
}

int fputs(const char *str, FILE *stream) {
    return sys_write(stream->fd, str, strlen(str));
}


size_t strlen(const char *str) {
    size_t ret = 0;

    for(; *str; ++str, ++ret)
        ;

    return ret;
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

void *memcpy(void *destination, const void *source, size_t num) {
    /*
     * Copies the values of num bytes from the location pointed to by source directly to the memory block pointed to by destination.
     * http://www.cplusplus.com/reference/cstring/memcpy
     */

    unsigned char *dst = (unsigned char *)destination;
    unsigned char *src = (unsigned char *)source;

    for (; num-- > 0; ++dst, ++src)
        *dst = *src;

    return destination;
}

char *strcpy(char * destination, const char *source) {
    char *src = (char *)source;
    char *dst = destination;

    while ((*(dst++) = *(src++)) != 0)
        ;

    return destination;
}

char *strdup(const char *str) {
    size_t len = strlen(str);
    char *copied = calloc(len, sizeof(char));

    return memcpy(copied, str, len);
}

void *calloc(size_t num, size_t size) {
    void *data = malloc(num * size);

    if (data == (void *)(-1)) {
        return NULL;  // failed to allocate memory
    }

    return memset(data, 0, num);
}


void *sbrk(long increment) {
    /*
     * increments the program's data space by `increment` bytes.
       Calling sbrk() with an increment of 0 can be used to find the current
       location of the program break.
     */

    void *current_break = (void *)sys_brk(0);  // pass invalid address on purpose to get current page break
    void *changed = (void *)sys_brk((unsigned long)(current_break + increment));

    if (changed == current_break) {
        // failed to allocate memory

        return (void *)(-1);
    }

    return current_break;
}


// `malloc` and `free` implementation. Taken from C&R book.

#define MIN_HDR_ALLOC 64

typedef size_t Align;

union header {
    struct {
        union header *next_block;
        size_t block_size;
    } block_info;
    Align x;
};

typedef union header Header;

static Header malloc_base;
static Header *malloc_free_space = NULL;

static Header *morecore(size_t nheaders) {
    char *mem_from_kernel;
    Header *up;

    if (nheaders < MIN_HDR_ALLOC)
        nheaders = MIN_HDR_ALLOC;

    mem_from_kernel = sbrk(nheaders * sizeof(Header));

    if (mem_from_kernel == (void *)(-1)) {
        // no memory left
        return NULL;
    }

    up = (Header *)mem_from_kernel;
    up->block_info.block_size = nheaders;

    free((void *)(up + 1));

    return malloc_free_space;
}

void *malloc(size_t nbytes) {
    Header *prev_ptr;
    size_t nheaders = (nbytes + sizeof(Header) - 1) / sizeof(Header) + 1;

    if ((prev_ptr = malloc_free_space) == NULL) {
        // no headers yet; create one
        malloc_base.block_info.next_block = malloc_free_space = prev_ptr = &malloc_base;
        malloc_base.block_info.block_size = 0;
    }

    for (Header *ptr = prev_ptr->block_info.next_block; ; prev_ptr = ptr, ptr = ptr->block_info.next_block) {
        if (ptr->block_info.block_size >= nheaders) {
            // there's enough memory
            if (ptr->block_info.block_size == nheaders) {
                prev_ptr->block_info.next_block = ptr->block_info.next_block;
            } else {
                ptr->block_info.block_size -= nheaders;
                ptr += ptr->block_info.block_size;
                ptr->block_info.block_size = nheaders;
            }

            malloc_free_space = prev_ptr;
            return (void *)(ptr + 1);
        }

        if (ptr == malloc_free_space) {
            // not enough blocks
            if ((ptr = morecore(nheaders)) == NULL) {
                // ran out of memory
                return NULL;
            }
        }
    }
}


void free(void *data) {
    Header *data_hdr = (Header *)data - 1;
    Header *ptr;

    for (ptr = malloc_free_space; !(data_hdr > ptr && data_hdr < ptr->block_info.next_block); ptr = ptr->block_info.next_block) {
        if (ptr >= ptr->block_info.next_block && (data_hdr > ptr || data_hdr < ptr->block_info.next_block)) {
            // the block is either at the beginning or at the end of the list
            break;
        }
    }

    // goto upstream neighbor
    if (data_hdr + data_hdr->block_info.block_size == ptr->block_info.next_block) {
        // merge two blocks
        data_hdr->block_info.block_size += ptr->block_info.next_block->block_info.block_size;
        data_hdr->block_info.next_block = ptr->block_info.next_block->block_info.next_block;
    } else {
        data_hdr->block_info.next_block = ptr->block_info.next_block;
    }

    // goto downstream neighbor
    if (ptr + ptr->block_info.block_size == data_hdr) {
        // merge two blocks
        ptr->block_info.block_size += data_hdr->block_info.block_size;
        ptr->block_info.next_block = data_hdr->block_info.next_block;
    } else {
        ptr->block_info.next_block = data_hdr;
    }

    malloc_free_space = ptr;

    // return memory to the kernel
    if (malloc_free_space->block_info.next_block == &malloc_base) {
        sbrk(-malloc_free_space->block_info.block_size - sizeof(Header));
        //sys_brk((unsigned long)malloc_free_space);
    }

    if (malloc_free_space == &malloc_base) {
        sbrk(malloc_base.block_info.block_size);
    }
}


static struct {
    void *buffer_begin, *buffer_current_end, *buffer_end;
} __malloc_data = {.buffer_begin=NULL, .buffer_current_end=NULL, .buffer_end=NULL};

void *_malloc(size_t size) {
    size_t alloc_size = size + size % 4 + sizeof(size_t);  // `sizeof(size_t)` to store area size
    char *retval = NULL;

    if (__malloc_data.buffer_begin == NULL) {
        // request more memory
        void *addr = sbrk(alloc_size + alloc_size / 2);

        if (addr == (void *)(-1)) {
            //failed to allocate memory
            return NULL;
        }

        __malloc_data.buffer_begin = addr;
        __malloc_data.buffer_current_end = addr + alloc_size;
        __malloc_data.buffer_end = __malloc_data.buffer_current_end + alloc_size / 2;
    } else {
        if (__malloc_data.buffer_end < __malloc_data.buffer_current_end + size) {
            void *addr = sbrk(alloc_size + alloc_size / 2);

            if (addr == (void *)(-1)) {
                //failed to allocate memory
                return NULL;
            }

            __malloc_data.buffer_current_end += alloc_size;
            __malloc_data.buffer_end = __malloc_data.buffer_current_end + alloc_size / 2;
        } else {
            __malloc_data.buffer_current_end += alloc_size;
        }
    }

    retval = __malloc_data.buffer_current_end - size;
    *(retval - sizeof(size_t)) = size;  // store size of this area for `free`

    return (void *)retval;
}

void _free(void *data) {
    if (
        (data == NULL)
        || (__malloc_data.buffer_begin == NULL)
        || (data < __malloc_data.buffer_begin)
        || (data > __malloc_data.buffer_current_end)
       )
    {
        return;
    }

    size_t size_to_free = *((char *)data - sizeof(size_t));

    __malloc_data.buffer_current_end = data - size_to_free - size_to_free % 4 - sizeof(size_t);

    if (__malloc_data.buffer_end - __malloc_data.buffer_current_end > FREE_THRESHOLD) {
        void *r = sbrk(__malloc_data.buffer_current_end - __malloc_data.buffer_end);

        if (r == (void *)(-1)) {
            return;
        }
    } else if ((__malloc_data.buffer_begin != NULL) && (__malloc_data.buffer_current_end == __malloc_data.buffer_begin)) {
        void *r = sbrk(__malloc_data.buffer_begin - __malloc_data.buffer_end);  // free everything

        if (r == (void *)(-1)) {
            return;
        }

        __malloc_data.buffer_begin = NULL;
    }
}

#undef FREE_THRESHOLD