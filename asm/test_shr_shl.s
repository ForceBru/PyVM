USE32

%include "definitions.h"

section .text
global _start

_start:
	mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message
    mov edx, message_len
    int 0x80

	mov eax, SYS_WRITE
    shl eax, 1
    shr eax, 1

    mov ecx, success
    mov edx, success_len
    int 0x80

    mov eax, SYS_EXIT
    mov ebx, 1
    shl ebx, 5
    shr ebx, 6
    int 0x80


message db "Testing shifts...", 10
message_len equ $ - message
success db "Success!", 10
success_len equ $ - success