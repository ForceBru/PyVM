USE32

%include "definitions.h"

section .text
global _start

_start:
    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_1
    mov edx, message_1_len
    int 0x80

    jmp success

_weird_stuff:
    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_error
    mov edx, message_error_len
    int 0x80

    mov eax, SYS_EXIT
    mov ebx, -1
    int 0x80

success:
    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_success
    mov edx, message_success_len
    int 0x80

exit:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80


section .data
    message_1 db "Testing unconditional jumps and interrupts...", 10
    message_1_len equ $ - message_1

    message_error db "We were supposed to jump over this, but we didn't!!!", 10
    message_error_len equ $ - message_error

    message_success db "Success!", 10
    message_success_len equ $ - message_success