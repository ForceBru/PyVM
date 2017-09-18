USE32

%include "definitions.h"

section .text
global _start

_start:
    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_1
    mov edx, message_1_len
    int 0x80 ; output the message

    mov edx, success
    lea ecx, [edx]
    mov edx, success_len
    int 0x80

exit:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80


section .data
    message_1 db "Testing lea...", 10
    message_1_len equ $ - message_1
    success db "Success!", 10
    success_len equ $ - success