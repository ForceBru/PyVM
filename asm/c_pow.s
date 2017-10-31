%include "startup.s"

; int pow(const int a, unsigned b) {
;     if (not b) return 1;
;     int result = a;
;     while (b-- > 1) {
;         result *= a;
;     }
;    return result;
; }
_Z3powij:
  mov ecx, DWORD [esp+4]
  mov eax, DWORD [esp+8]
  test eax, eax
  je .L4
  lea edx, [eax-1]
  cmp eax, 1
  mov eax, ecx
  jbe .L5
.L3:
  imul eax, ecx
  dec edx
  jne .L3
  ret
.L4:
  mov eax, 1
.L5:
  ret

main:
  push ebp
  mov ebp, esp
  push 4
  push 5
  call _Z3powij
  add esp, 8
  leave
  ret