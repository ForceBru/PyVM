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

    mov [output], BYTE 79     ; ASCII char 'O'
    mov [output + 1], BYTE 75 ; ASCII char 'K'
    mov [output + 2], BYTE 10 ; ASCII newline

    ; output the word before changes
    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, output
    mov edx, 3
    int 0x80 ; should print 'OK\n'

    sub [output + 1], BYTE 3 ; now the second char should be 'H'

    ; output the word after changes
    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, output
    mov edx, 3
    int 0x80 ; should print 'OH\n'

    add [output + 1], BYTE 3 ; now the second char should be 'K'

    ; output the word after changes, now it should be reverted to 'OK\n'
    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, output
    mov edx, 3
    int 0x80 ; should print 'OK\n'

    jmp exit

exit:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80


section .bss
    output resb 3 ; two letters + '\n'

section .data
    message_1 db "Testing add and sub...", 10
    message_1_len equ $ - message_1