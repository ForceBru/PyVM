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

    ; BEGIN save registers
    push eax
    push ecx
    push edx
    ; END save registers

    ; no parameters

    call print

    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_success
    mov edx, message_success_len
    int 0x80

    jmp exit

_weird_stuff:
    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_error_1
    mov edx, message_error_1_len
    int 0x80

print:
    ; BEGIN new stack frame
    push ebp
    mov ebp, esp
    ; END new stack frame

    ; no local variables

    ; BEGIN save registers
    ; (we don't use them, this is just for completeness)
    push ebx
    push edi
    push esi
    ; END save registers

    mov eax, SYS_WRITE
    mov ebx, STDOUT
    mov ecx, message_print
    mov edx, message_print_len
    int 0x80

    ; return value
    mov eax, 0

    ; BEGIN restore registers
    pop esi
    pop edi
    pop ebx
    ; END restore registers

    ; no local variables

    ; restore base pointer
    pop ebp

    ; return control to caller
    ret

exit:
    mov eax, SYS_EXIT
    mov ebx, 0
    int 0x80

section .data
    message_1 db "Testing call and ret...", 10
    message_1_len equ $ - message_1

    message_error_1 db "This was not supposed to be executed!", 10
    message_error_1_len equ $ - message_error_1

    message_print db "Inside the function...", 10
    message_print_len equ $ - message_print

    message_success db "Inside _start again, great!", 10
    message_success_len equ $ - message_success