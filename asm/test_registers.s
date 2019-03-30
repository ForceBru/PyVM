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
    mov ebx, 2
    jne fail

    jmp success

fail:
    ; the return code is stored in ebx
    mov eax, 1
    int 0x80

success:
    mov ebx, 0
    jmp fail