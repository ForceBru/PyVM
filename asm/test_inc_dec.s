
_start:
	mov eax, 1
	xor ecx, ecx
	inc ecx
	dec ecx
	test ecx, ecx
	jnz fail
	
success:
	xor ebx, ebx
	int 0x80
	
fail:
	mov ebx, 1
	int 0x80
