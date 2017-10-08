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

	; remember that this is little-endian, so the bytes are reversed
    mov al, BYTE [A] ; first byte
    mov bl, BYTE [B]

    add al, bl ; this generates a carry

    mov BYTE [C], al ; save the first byte

    mov al, BYTE [A + 1] ; second byte
    mov bl, BYTE [B + 1]

    adc al, bl ; use the carry

    mov BYTE [C + 1], al ; save the second byte

    mov al, 0 ; clear al

    adc al, 0 ; get the carry

    mov BYTE [C + 2], al ; save the third byte

	jmp check_byte_1

check_byte_1:
    cmp BYTE [C], 11000010b
    je check_byte_2
    jmp fail

check_byte_2:
	cmp BYTE [C + 1], 00100111b
	je check_byte_3
	add BYTE [message_fail + 5], 1
	jmp fail

check_byte_3:
	cmp BYTE [C + 2], 00000001b
	je success
	add BYTE [message_fail + 5], 2
	jmp fail

success:
	mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_success
    mov edx, message_success_len
    int 0x80

    jmp exit

fail:
	mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_fail
    mov edx, message_fail_len
    int 0x80

exit:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80

section .bss
	C: resb 3 ; the result of (A + B) is 00000001 00100111 11000010 == 75714

section .data
	A: dw 1010101011001011b ; 43723
	B: dw 0111110011110111b ; 31991

    message_1 db "Testing adc...",10,"Adding two large numbers...", 10
    message_1_len equ $ - message_1

    message_fail db "Byte 1 fail!", 10
    message_fail_len equ $ - message_fail

    message_success db "Success!", 10
    message_success_len equ $ - message_success

