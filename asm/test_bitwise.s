USE32

%include "definitions.h"

section .text
global _start

_start:
	jmp test_and

_exit:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80

test_and:
	mov ecx, message_and
    mov edx, message_and_len
    call print_testing

	mov eax, 5
	mov ebx, 6
	and eax, ebx

	cmp eax, 4
	je test_or
	jmp print_fail

test_or:
	mov ecx, message_or
    mov edx, message_or_len
    call print_testing

	mov eax, 5
	mov ebx, 6
	or eax, ebx

	cmp eax, 7
	je test_xor
	jmp print_fail

test_xor:
	mov ecx, message_xor
    mov edx, message_xor_len
    call print_testing

	mov eax, 5
	mov ebx, 6
	xor eax, ebx

	cmp eax, 3
	je test_not
	jmp print_fail

test_not:
	mov ecx, message_not
    mov edx, message_not_len
    call print_testing

	mov eax, 5
	not eax

	cmp eax, -6
	je test_neg
	jmp print_fail

test_neg:
	mov ecx, message_neg
    mov edx, message_neg_len
    call print_testing

	mov eax, 5
	neg eax

	cmp eax, -5
	je success
	jmp print_fail

print_testing:
	push ebp
    mov ebp, esp

    push eax
    push ebx

	mov eax, SYS_WRITE
    mov ebx, STDOUT
    int 0x80

    pop ebx
    pop eax
    pop ebp

    ret

print_fail:
	mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_fail
    mov edx, message_fail_len
    int 0x80

    jmp _exit

success:
	mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_success
    mov edx, message_success_len
    int 0x80

    jmp _exit

section .data
    message_1 db "Testing bitwise operations...", 10
    message_1_len equ $ - message_1

    message_and db "Testing AND...", 10
    message_and_len equ $ - message_and

    message_or db "Testing OR...", 10
    message_or_len equ $ - message_or

    message_xor db "Testing XOR...", 10
    message_xor_len equ $ - message_xor

    message_not db "Testing NOT...", 10
    message_not_len equ $ - message_not

    message_neg db "Testing NEG...", 10
    message_neg_len equ $ - message_neg

    message_fail db "failed!", 10
    message_fail_len equ $ - message_fail

    message_success db "All tests succeeded!!", 10
    message_success_len equ $ - message_success