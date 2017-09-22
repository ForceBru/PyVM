%include "startup.s"

align	4, db 0x90

change_data:
	push	ebp
	mov	ebp, esp
	push	eax
	mov	eax, dword  [ebp + 8]
	mov	dword  [ebp - 4], eax
	mov	eax, dword  [ebp - 4]
	mov	dword  [eax], 1
	add	esp, 4
	pop	ebp
	ret

align	4, db 0x90

main:
	push	ebp
	mov	ebp, esp
	sub	esp, 24
	lea	eax, [ebp - 8]
	mov	dword  [ebp - 4], 0
	mov	dword  [ebp - 8], 5
	mov	dword  [esp], eax
	call	change_data
	mov	eax, dword  [ebp - 8]
	add	esp, 24
	pop	ebp
	ret
