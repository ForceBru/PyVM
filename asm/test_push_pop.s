USE32

%include "definitions.h"

section .text
global _start

_start:
    mov [output + 2], BYTE 10 ; new line

    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_1
    mov edx, message_1_len
    int 0x80 ; output the message

    push BYTE 48 ; ASCII char '0'
    push BYTE 49 ; ASCII char '1'

    pop ax ; get two bytes, in reverse order
    mov BYTE [output], ah
    mov BYTE [output + 1], al

    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, output
    mov edx, 3
    int 0x80 ; should print '01\n'

    jmp exit

exit:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80


section .bss
    output resb 3; two letters + '\n'

section .data
    message_1 db "Testing push and pop...", 10
    message_1_len equ $ - message_1