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

test_two_op_16bit:
    sub esp, 2 ; allocate room for 2 bytes

    mov ax, 0xfa13 ; prime number
    mov WORD [esp], 0xfa21 ; next prime number
    imul ax, WORD [esp]
    inc ebx
    cmp ax, (0xfa13 * 0xfa21) & 0xFFFF
    jne error

    mov ax, -0xfa13 ; prime number
    mov WORD [esp], 0xfa21 ; next prime number
    imul ax, WORD [esp]
    inc ebx
    cmp ax, (-0xfa13 * 0xfa21) & 0xFFFF
    jne error

    mov ax, 0xfa13 ; prime number
    mov WORD [esp], -0xfa21 ; next prime number
    imul ax, WORD [esp]
    inc ebx
    cmp ax, (0xfa13 * -0xfa21) & 0xFFFF
    jne error

    mov ax, -0xfa13 ; prime number
    mov WORD [esp], -0xfa21 ; next prime number
    imul ax, WORD [esp]
    inc ebx
    cmp ax, (-0xfa13 * -0xfa21) & 0xFFFF
    jne error

    add esp, 2 ; return 2 bytes

test_two_op_32bit:
    sub esp, 4 ; allocate room for 4 bytes

    mov eax, 0xe219 ; prime number
    mov DWORD [esp], 0xe22b ; next prime number
    imul eax, DWORD [esp]
    inc ebx
    cmp eax, 0xe219 * 0xe22b
    jne error

    mov eax, -0xe219 ; prime number
    mov DWORD [esp], 0xe22b ; next prime number
    imul eax, DWORD [esp]
    inc ebx
    cmp eax, -0xe219 * 0xe22b
    jne error

    mov eax, 0xe219 ; prime number
    mov DWORD [esp], -0xe22b ; next prime number
    imul eax, DWORD [esp]
    inc ebx
    cmp eax, 0xe219 * -0xe22b
    jne error

    mov eax, -0xe219 ; prime number
    mov DWORD [esp], -0xe22b ; next prime number
    imul eax, DWORD [esp]
    inc ebx
    cmp eax, -0xe219 * -0xe22b
    jne error

    add esp, 4

test_three_op_16_8bit:
    sub esp, 2

    mov WORD [esp], 654
    imul ax, WORD [esp], 3
    inc ebx
    cmp ax, (654 * 3) & 0xFFFF
    jne error

    mov WORD [esp], -654
    imul ax, WORD [esp], 3
    inc ebx
    cmp ax, (-654 * 3) & 0xFFFF
    jne error

    mov WORD [esp], 654
    imul ax, WORD [esp], -3
    inc ebx
    cmp ax, (654 * -3) & 0xFFFF
    jne error

    mov WORD [esp], -654
    imul ax, WORD [esp], -3
    inc ebx
    cmp ax, (-654 * -3) & 0xFFFF
    jne error

    add esp, 2

test_three_op_16_16bit:
    sub esp, 2

    mov WORD [esp], 654
    imul ax, WORD [esp], 867
    inc ebx
    cmp ax, (654 * 867) & 0xFFFF
    jne error

    mov WORD [esp], -654
    imul ax, WORD [esp], 867
    inc ebx
    cmp ax, (-654 * 867) & 0xFFFF
    jne error

    mov WORD [esp], 654
    imul ax, WORD [esp], -867
    inc ebx
    cmp ax, (654 * -867) & 0xFFFF
    jne error

    mov WORD [esp], -654
    imul ax, WORD [esp], -867
    inc ebx
    cmp ax, (-654 * -867) & 0xFFFF
    jne error

    add esp, 2

test_three_op_32_8bit:
    sub esp, 4

    mov DWORD [esp], 1336375030
    imul eax, DWORD [esp], 153
    inc ebx
    cmp eax, (1336375030 * 153) & 0xFFFFFFFF
    jne error

    mov DWORD [esp], -1336375030
    imul eax, DWORD [esp], 153
    inc ebx
    cmp eax, (-1336375030 * 153) & 0xFFFFFFFF
    jne error

    mov DWORD [esp], 1336375030
    imul eax, DWORD [esp], -153
    inc ebx
    cmp eax, (1336375030 * -153) & 0xFFFFFFFF
    jne error

    mov DWORD [esp], -1336375030
    imul eax, DWORD [esp], -153
    inc ebx
    cmp eax, (-1336375030 * -153) & 0xFFFFFFFF
    jne error

    add esp, 4

test_three_op_32_16bit:
    sub esp, 4

    mov DWORD [esp], 1336375030
    imul eax, DWORD [esp], 467
    inc ebx
    cmp eax, (1336375030 * 467) & 0xFFFFFFFF
    jne error

    mov DWORD [esp], -1336375030
    imul eax, DWORD [esp], 467
    inc ebx
    cmp eax, (-1336375030 * 467) & 0xFFFFFFFF
    jne error

    mov DWORD [esp], 1336375030
    imul eax, DWORD [esp], -467
    inc ebx
    cmp eax, (1336375030 * -467) & 0xFFFFFFFF
    jne error

    mov DWORD [esp], -1336375030
    imul eax, DWORD [esp], -467
    inc ebx
    cmp eax, (-1336375030 * -467) & 0xFFFFFFFF
    jne error

    add esp, 4

success:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80

error:
    mov eax, SYS_EXIT
    ; ebx already set up
    int 0x80