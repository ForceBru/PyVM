USE32

%include "definitions.h"

section .text
global _start

_start:
	mov eax, SYS_WRITE
    mov ebx, STDOUT

    xchg eax, ebx

    mov ecx, message_1
    mov edx, message_1_len

    xchg eax, ebx
    int 0x80

	mov eax, 1000
	xor ebx, ebx

	loop:
		test eax, eax
		jz _exit
		dec eax
		inc ebx
		jmp loop

_exit:
	mov eax, SYS_EXIT
	int 0x80


message_1 db "Testing xchg...",10
message_1_len equ $ - message_1