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

sys_write:
    push    ebp
    mov     ebp, esp
    sub     esp, 12 ; 4 + 4 + 4

    mov eax, 4 ; sys_write
    mov ebx, dword [ebp + 8]
    mov ecx, dword [ebp + 12]
    mov edx, dword [ebp + 16]
    int 0x80

    mov eax, ebx

    leave
    ret