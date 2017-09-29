%include "startup.s"

align	16, db 0x90

main:
	push	ebp
	mov	ebp, esp
	sub	esp, 8
	mov	dword [ebp - 4], 0
	mov	dword [ebp - 8], 0
.LBB0_1:
	cmp	dword [ebp - 8], 10
	jge	.LBB0_4

	jmp	.LBB0_3
.LBB0_3:
	mov	eax, dword [ebp - 8]
	add	eax, 1
	mov	dword [ebp - 8], eax
	jmp	.LBB0_1
.LBB0_4:
	mov	eax, dword [ebp - 8]
	add	esp, 8
	pop	ebp
	ret