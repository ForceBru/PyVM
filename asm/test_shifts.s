USE32

%include "definitions.h"

section .text
global _start

_start:
    mov ebx, 1 ; error code

test_shl:
    mov eax, 0xffffffff
    shl eax, 5
    cmp eax, 0xffffffe0
    jne error

    mov eax, 0x00ffffff
    shl eax, 5
    cmp eax, 0x1fffffe0
    jne error

    mov eax, 0xffffffff
    shl eax, 1
    inc ebx
    cmp eax, 0xfffffffe
    jne error

    mov eax, 0x00ffffff
    shl eax, 1
    inc ebx
    cmp eax, 0x01fffffe
    jne error

    mov eax, 0xffffffff
    mov cl, 16
    shl eax, cl
    inc ebx
    cmp eax, 0xffff0000
    jne error

    mov eax, 0x00ffffff
    mov cl, 16
    shl eax, cl
    inc ebx
    cmp eax, 0xffff0000
    jne error

test_shr:
    mov eax, 0xffffffff
    shr eax, 5
    inc ebx
    cmp eax, 0x07ffffff
    jne error

    mov eax, 0x00ffffff
    shr eax, 5
    inc ebx
    cmp eax, 0x0007ffff
    jne error

    mov eax, 0xffffffff
    shr eax, 1
    inc ebx
    cmp eax, 0x7fffffff
    jne error

    mov eax, 0x00ffffff
    shr eax, 1
    inc ebx
    cmp eax, 0x007fffff
    jne error

    mov eax, 0xffffffff
    mov cl, 16
    shr eax, cl
    inc ebx
    cmp eax, 0x0000ffff
    jne error

    mov eax, 0x00ffffff
    mov cl, 16
    shr eax, cl
    inc ebx
    cmp eax, 0x000000ff
    jne error

test_sar:
    mov eax, 0xffffffff
    sar eax, 5
    inc ebx
    cmp eax, 0xffffffff
    jne error

    mov eax, 0x00ffffff
    sar eax, 5
    inc ebx
    cmp eax, 0x0007ffff
    jne error

    mov eax, 0xffffffff
    sar eax, 1
    inc ebx
    cmp eax, 0xffffffff
    jne error

    mov eax, 0x00ffffff
    sar eax, 1
    inc ebx
    cmp eax, 0x007fffff
    jne error

    mov eax, 0xffffffff
    mov cl, 16
    sar eax, cl
    inc ebx
    cmp eax, 0xffffffff
    jne error

    mov eax, 0x00ffffff
    mov cl, 16
    sar eax, cl
    inc ebx
    cmp eax, 0x000000ff
    jne error

success:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80

error:
    mov eax, SYS_EXIT
    ; ebx already set up
    int 0x80