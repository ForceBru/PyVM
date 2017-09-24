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

	mov eax, 5
	mov ebx, 2

	test eax, ebx
	jz success
	jmp fail

_exit:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80

success:
	mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_success
    mov edx, message_success_len
    int 0x80

    jmp _exit

fail:
	mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_fail
    mov edx, message_fail_len
    int 0x80

    jmp _exit


section .data
	message_1 db "Testing test...", 10
	message_1_len equ $ - message_1

	message_success db "Success!", 10
	message_success_len equ $ - message_success

	message_fail db "Test failed!", 10
	message_fail_len equ $ - message_fail