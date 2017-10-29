%include "definitions.h"
%include "startup.s"

; int main(void) {
;     volatile int a = -5, b = 56;
;     volatile long c = 256, d = -542;
;     if (b / a != -12) return 1;
;     if (b % a != -4) return 2;
;     if (d / c != -3) return 3;
;     if (d % c != 226) return 4;
;     return 0;
; }

main:
  mov eax, SYS_WRITE
  mov ebx, STDOUT
  mov ecx, message
  mov edx, message_len
  int 0x80

_main:
  push ebp
  mov ebp, esp
  sub esp, 16
  mov DWORD [ebp-4], -5
  mov DWORD [ebp-8], 56
  mov DWORD [ebp-12], 256
  mov DWORD [ebp-16], -542
  mov eax, DWORD [ebp-8]
  mov ecx, DWORD [ebp-4]
  cdq
  idiv ecx
  cmp eax, -12
  je .L2
  mov eax, 1
  jmp .L3
.L2:
  mov eax, DWORD [ebp-8]
  mov ecx, DWORD [ebp-4]
  cdq
  idiv ecx
  mov eax, edx
  cmp eax, -4
  je .L4
  mov eax, 2
  jmp .L3
.L4:
  mov eax, DWORD [ebp-16]
  mov ecx, DWORD [ebp-12]
  cdq
  idiv ecx
  cmp eax, -3
  je .L5
  mov eax, 3
  jmp .L3
.L5:
  mov eax, DWORD [ebp-16]
  mov ecx, DWORD [ebp-12]
  cdq
  idiv ecx
  mov eax, edx
  cmp eax, 226
  je .L6
  mov eax, 4
  jmp .L3
.L6:
  mov eax, 0
.L3:
  leave
  ret


message db "Testing idiv...", 10
message_len equ $ - message