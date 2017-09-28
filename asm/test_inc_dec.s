USE32

%include "definitions.h"

section .text
global _start

_start:
	mov eax, 0
	dec eax
	inc eax
	cmp eax, 0
	je success
	jmp fail
	
success:
	mov eax, SYS_EXIT
	mov ebx, 0
	int 0x80
	
fail:
	mov eax, SYS_EXIT
	mov ebx, 1
	int 0x80
