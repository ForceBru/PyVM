%include "definitions.h"
%include "startup.s"

; int main(void) {
;     volatile unsigned a = 5, b = 56;
;     volatile unsigned long c = 256, d = 542;
;     if (a * b != 280) return 1;
;     if (c * d != 138752) return 2;
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

  mov DWORD [ebp-4], 5
  mov DWORD [ebp-8], 56
  mov DWORD [ebp-12], 256
  mov DWORD [ebp-16], 542
  mov edx, DWORD [ebp-4]
  mov eax, DWORD [ebp-8]
  imul eax, edx
  cmp eax, 280
  je .L2
  mov eax, 1
  jmp .L3
.L2:
  mov edx, DWORD [ebp-12]
  mov eax, DWORD [ebp-16]
  imul eax, edx
  cmp eax, 138752
  je .L4
  mov eax, 2
  jmp .L3
.L4:
  mov eax, 0
.L3:
  leave
  ret


message db "Testing imul...", 10
message_len equ $ - message