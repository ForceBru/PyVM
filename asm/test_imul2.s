USE32

%include "definitions.h"

section .text
global _start

_start:
    mov ebx, 0 ; error code

test_single_op_8bit:
    mov al, 0x05
    mov ch, 0x05
    imul ch
    inc ebx
    cmp ax, 0x05 * 0x05
    jne error

    mov al, -0x05
    mov ch, 0x05
    imul ch
    inc ebx
    cmp ax, -0x05 * 0x05
    jne error

    mov al, -0x05
    mov ch, -0x05
    imul ch
    inc ebx
    cmp ax, -0x05 * -0x05
    jne error

    mov al, 0x05
    mov ch, -0x05
    imul ch
    inc ebx
    cmp ax, 0x05 * -0x05
    jne error

test_single_op_16bit:
    mov ax, 0x8dd ; prime number
    mov cx, 0x8e1 ; next prime number
    imul cx
    inc ebx
    cmp dx, (0x8dd * 0x8e1) >> 16
    jne error
    cmp ax, (0x8dd * 0x8e1) & 0xFFFF
    jne error

    mov ax, -0x8dd ; prime number
    mov cx, 0x8e1 ; next prime number
    imul cx
    inc ebx
    cmp dx, (-0x8dd * 0x8e1) >> 16
    jne error
    cmp ax, (-0x8dd * 0x8e1) & 0xFFFF
    jne error

    mov ax, 0x8dd ; prime number
    mov cx, -0x8e1 ; next prime number
    imul cx
    inc ebx
    cmp dx, (0x8dd * -0x8e1) >> 16
    jne error
    cmp ax, (0x8dd * -0x8e1) & 0xFFFF
    jne error

    mov ax, -0x8dd ; prime number
    mov cx, -0x8e1 ; next prime number
    imul cx
    inc ebx
    cmp dx, (-0x8dd * -0x8e1) >> 16
    jne error
    cmp ax, (-0x8dd * -0x8e1) & 0xFFFF
    jne error

test_single_op_32bit:
    mov eax, 0x196bb ; prime number
    mov ecx, 0x196d3 ; next prime number
    imul ecx
    inc ebx
    cmp edx, (0x196bb * 0x196d3) >> 32
    jne error
    cmp eax, (0x196bb * 0x196d3) & 0xFFFFFFFF
    jne error

    mov eax, -0x196bb ; prime number
    mov ecx, 0x196d3 ; next prime number
    imul ecx
    inc ebx
    cmp edx, (-0x196bb * 0x196d3) >> 32
    jne error
    cmp eax, (-0x196bb * 0x196d3) & 0xFFFFFFFF
    jne error

    mov eax, 0x196bb ; prime number
    mov ecx, -0x196d3 ; next prime number
    imul ecx
    inc ebx
    cmp edx, (0x196bb * -0x196d3) >> 32
    jne error
    cmp eax, (0x196bb * -0x196d3) & 0xFFFFFFFF
    jne error

    mov eax, -0x196bb ; prime number
    mov ecx, -0x196d3 ; next prime number
    imul ecx
    inc ebx
    cmp edx, (-0x196bb * -0x196d3) >> 32
    jne error
    cmp eax, (-0x196bb * -0x196d3) & 0xFFFFFFFF
    jne error

success:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80

error:
    mov eax, SYS_EXIT
    ; ebx already set up
    int 0x80