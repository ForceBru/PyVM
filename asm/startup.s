USE32

section .text
global _start
_start:
    call main

    jmp _exit

_exit:
    mov ebx, eax
    mov eax, 1
    int 0x80