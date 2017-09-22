	.text
	.intel_syntax noprefix
	.file	"pointers.c"
	.globl	change_data
	.p2align	4, 0x90
	.type	change_data,@function
change_data:                            # @change_data
# BB#0:
	push	ebp
	mov	ebp, esp
	push	eax
	mov	eax, dword ptr [ebp + 8]
	mov	dword ptr [ebp - 4], eax
	mov	eax, dword ptr [ebp - 4]
	mov	dword ptr [eax], 1
	add	esp, 4
	pop	ebp
	ret
.Lfunc_end0:
	.size	change_data, .Lfunc_end0-change_data

	.globl	main
	.p2align	4, 0x90
	.type	main,@function
main:                                   # @main
# BB#0:
	push	ebp
	mov	ebp, esp
	sub	esp, 24
	lea	eax, [ebp - 8]
	mov	dword ptr [ebp - 4], 0
	mov	dword ptr [ebp - 8], 5
	mov	dword ptr [esp], eax
	call	change_data
	mov	eax, dword ptr [ebp - 8]
	add	esp, 24
	pop	ebp
	ret
.Lfunc_end1:
	.size	main, .Lfunc_end1-main


	.ident	"Apple LLVM version 8.1.0 (clang-802.0.42)"
	.section	".note.GNU-stack","",@progbits
