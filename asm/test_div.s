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

    call main

	push eax
    jmp exit

main:
  push ebp
  mov ebp, esp
  sub esp, 32
  mov DWORD  [ebp-4], 5
  mov DWORD  [ebp-8], 56
  mov DWORD  [ebp-12], 280
  mov DWORD  [ebp-16], 256
  mov DWORD  [ebp-20], 542
  mov DWORD  [ebp-24], 138752
  mov eax, DWORD  [ebp-8]
  mov ecx, DWORD  [ebp-4]
  mov edx, 0
  div ecx
  cmp eax, 11
  je .L2
  mov eax, 1
  jmp .L3
.L2:
  mov eax, DWORD  [ebp-8]
  mov ecx, DWORD  [ebp-4]
  mov edx, 0
  div ecx
  mov eax, edx
  cmp eax, 1
  je .L4
  mov eax, 2
  jmp .L3
.L4:
  mov eax, DWORD  [ebp-20]
  mov ecx, DWORD  [ebp-16]
  mov edx, 0
  div ecx
  cmp eax, 2
  je .L5
  mov eax, 3
  jmp .L3
.L5:
  mov eax, DWORD  [ebp-20]
  mov ecx, DWORD  [ebp-16]
  mov edx, 0
  div ecx
  mov eax, edx
  cmp eax, 30
  je .L6
  mov eax, 4
  jmp .L3
.L6:
  mov eax, 0
.L3:
  leave
  ret

exit:
    mov eax, SYS_EXIT
    pop ebx
    int 0x80


section .data
    message_1 db "Testing div...", 10
    message_1_len equ $ - message_1
    message_fail_rm8 db "Division with r/m8 failed!", 10
    message_fail_rm8_len equ $ - message_fail_rm8
    message_fail_rm db "Division with r/m failed!", 10
    message_fail_rm_len equ $ - message_fail_rm
    message_success db "Success!", 10
    message_success_len equ $ - message_success