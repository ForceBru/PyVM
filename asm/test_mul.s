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

test_rm8:
    mov al, 4
    mov bl, 9
    mul bl

    cmp ax, 36
    jne fail_rm8

test_rm:
	mov ax, 4563
	mov bx, 7531

	mul bx

	cmp dx, 0x020c
	jne fail_rm

	cmp ax, 0x5a31
	jne fail_rm

	jmp success

fail_rm8:
	mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_fail_rm8
    mov edx, message_fail_rm8_len
    int 0x80

    mov ebx, 1

fail_rm:
	mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_fail_rm
    mov edx, message_fail_rm_len
    int 0x80

    mov ebx, 2

success:
	mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_success
    mov edx, message_success_len
    int 0x80

    mov ebx, 0

exit:
    mov eax, SYS_EXIT
    int 0x80


section .data
    message_1 db "Testing mul...", 10
    message_1_len equ $ - message_1
    message_fail_rm8 db "Multiplication with r/m8 failed!", 10
    message_fail_rm8_len equ $ - message_fail_rm8
    message_fail_rm db "Multiplication with r/m failed!", 10
    message_fail_rm_len equ $ - message_fail_rm
    message_success db "Success!", 10
    message_success_len equ $ - message_success