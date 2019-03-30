USE32

%include "definitions.h"

section .text
global _start

_start:
    mov ecx, 0x12345678 ; 4-byte value
    movzx ebx, cx
    cmp ebx, 0x00005678
    mov ebx, 1
    jne fail

    movzx ebx, ch
    cmp ebx, 0x00000056
    mov ebx, 2
    jne fail

    movzx ebx, cl
    cmp ebx, 0x00000078
    mov ebx, 3
    jne fail

    mov dx, 0x0123 ; 2-byte value

    movzx ebx, dx
    cmp ebx, 0x00000123
    mov ebx, 4
    jne fail

    movzx ebx, dh
    cmp ebx, 0x00000001
    mov ebx, 5
    jne fail

    movzx ebx, dl
    cmp ebx, 0x00000023
    mov ebx, 6
    jne fail

    mov dl, 0x99 ; 1-byte value

    movzx ebx, dx
    cmp ebx, 0x00000199
    mov ebx, 7
    jne fail

    movzx ebx, dh
    cmp ebx, 0x00000001
    mov ebx, 8
    jne fail

    movzx ebx, dl
    cmp ebx, 0x00000099
    mov ebx, 9
    jne fail

success:
    mov ebx, 0

fail:
    ; the return code is already in ebx
    mov eax, 1
    int 0x80