%include "startup.s"

_abs:
  push ebp
  mov ebp, esp
  sub esp, 8
  mov eax, DWORD [ebp+8]
  mov DWORD [ebp-8], eax
  mov eax, DWORD [ebp+12]
  mov DWORD [ebp-4], eax
  cmp DWORD [ebp-4], 0
  jns .L2
  mov eax, DWORD [ebp-8]
  mov edx, DWORD [ebp-4]
  neg eax
  adc edx, 0
  neg edx
  jmp .L3
.L2:
  mov eax, DWORD [ebp-8]
  mov edx, DWORD [ebp-4]
.L3:
  leave
  ret
pow:
  push ebp
  mov ebp, esp
  push esi
  push ebx
  sub esp, 56
  mov eax, DWORD [ebp+8]
  mov DWORD [ebp-48], eax
  mov eax, DWORD [ebp+12]
  mov DWORD [ebp-44], eax
  mov eax, DWORD [ebp+16]
  mov DWORD [ebp-56], eax
  mov eax, DWORD [ebp+20]
  mov DWORD [ebp-52], eax
  cmp DWORD [ebp-52], 0
  jns .L5
  mov eax, -1
  mov edx, -1
  jmp .L6
.L5:
  mov eax, DWORD [ebp-56]
  xor ah, 0
  mov edx, eax
  mov eax, DWORD [ebp-52]
  xor ah, 0
  mov ecx, eax
  mov eax, ecx
  or eax, edx
  test eax, eax
  jne .L7
  mov eax, 1
  mov edx, 0
  jmp .L6
.L7:
  mov eax, DWORD [ebp-44]
  shr eax, 31
  movzx eax, al
  mov DWORD [ebp-28], eax
  push DWORD [ebp-44]
  push DWORD [ebp-48]
  call _abs
  add esp, 8
  mov DWORD [ebp-48], eax
  mov DWORD [ebp-44], edx
  mov eax, DWORD [ebp-48]
  mov edx, DWORD [ebp-44]
  mov DWORD [ebp-40], eax
  mov DWORD [ebp-36], edx
  mov DWORD [ebp-16], 0
  mov DWORD [ebp-12], 0
.L13:
  mov eax, DWORD [ebp-16]
  mov edx, DWORD [ebp-12]
  cmp edx, DWORD [ebp-52]
  jg .L8
  cmp edx, DWORD [ebp-52]
  jl .L15
  cmp eax, DWORD [ebp-56]
  jnb .L8
.L15:
  mov DWORD [ebp-24], 0
  mov DWORD [ebp-20], 0
.L12:
  mov eax, DWORD [ebp-24]
  mov edx, DWORD [ebp-20]
  cmp edx, DWORD [ebp-36]
  jg .L10
  cmp edx, DWORD [ebp-36]
  jl .L16
  cmp eax, DWORD [ebp-40]
  jnb .L10
.L16:
  mov eax, DWORD [ebp-40]
  mov edx, DWORD [ebp-36]
  add DWORD [ebp-48], eax
  adc DWORD [ebp-44], edx
  add DWORD [ebp-24], 1
  adc DWORD [ebp-20], 0
  jmp .L12
.L10:
  add DWORD [ebp-16], 1
  adc DWORD [ebp-12], 0
  jmp .L13
.L8:
  cmp DWORD [ebp-28], 0
  je .L14
  mov eax, DWORD [ebp-56]
  and eax, 1
  mov DWORD [ebp-64], eax
  mov eax, DWORD [ebp-52]
  and eax, 0
  mov DWORD [ebp-60], eax
  mov eax, DWORD [ebp-64]
  mov edx, DWORD [ebp-60]
  mov ecx, eax
  xor ch, 0
  mov ebx, ecx
  mov eax, edx
  xor ah, 0
  mov esi, eax
  mov eax, esi
  or eax, ebx
  test eax, eax
  je .L14
  mov eax, DWORD [ebp-48]
  mov edx, DWORD [ebp-44]
  neg eax
  adc edx, 0
  neg edx
  jmp .L6
.L14:
  mov eax, DWORD [ebp-48]
  mov edx, DWORD [ebp-44]
.L6:
  lea esp, [ebp-8]
  pop ebx
  pop esi
  pop ebp
  ret
main:
  lea ecx, [esp+4]
  and esp, -8
  push DWORD [ecx-4]
  push ebp
  mov ebp, esp
  push ecx
  sub esp, 4
  push 0
  push 4
  push 0
  push 5
  call pow
  add esp, 16
  mov ecx, DWORD [ebp-4]
  leave
  lea esp, [ecx-4]
  ret