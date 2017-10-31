%include "startup.s"

_Z3absj:
  push ebp
  mov ebp, esp
  mov eax, DWORD [ebp+8]
  pop ebp
  ret
_Z3powij:
  push ebp
  mov ebp, esp
  sub esp, 16
  cmp DWORD [ebp+12], 0
  jne .L4
  mov eax, 1
  jmp .L5
.L4:
  cmp DWORD [ebp+12], 1
  jne .L6
  mov eax, DWORD [ebp+8]
  jmp .L5
.L6:
  mov eax, DWORD [ebp+8]
  mov DWORD [ebp-4], eax
.L8:
  cmp DWORD [ebp+12], 1
  jbe .L7
  mov eax, DWORD [ebp+8]
  imul eax, DWORD [ebp-4]
  mov DWORD [ebp+8], eax
  dec DWORD [ebp+12]
  jmp .L8
.L7:
  mov eax, DWORD [ebp+8]
.L5:
  leave
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