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

    cmp eax, message_1_len
    je test_jne
    jmp fail

exit:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80

test_jne:
	; BEGIN save registers
    push eax
    push ecx
    push edx
    ; END save registers

    call print

    ; BEGIN restore registers
    pop edx
    pop ecx
    pop eax
    ; END restore registers

	cmp eax, STDOUT
	jne test_jle
    jmp fail

test_jle:
	call print

	mov eax, 5
	cmp eax, 6
	jle success
	jmp fail

success:
	call print

	jmp exit

print:
	push ebp
    mov ebp, esp

    push ebx
    push edi
    push esi

    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_success
    mov edx, message_success_len
    int 0x80

    mov eax, 0

    pop esi
    pop edi
    pop ebx

    pop ebp

    ret

fail:
	mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_fail
    mov edx, message_fail_len
    int 0x80

    jmp exit

section .data
    message_1 db "Testing cmp and jcc...", 10
    message_1_len equ $ - message_1

    message_success db "Success!", 10
    message_success_len equ $ - message_success

    message_fail db "Failed!", 10
    message_fail_len equ $ - message_fail