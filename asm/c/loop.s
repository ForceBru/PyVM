	.text
	.intel_syntax noprefix
	.file	"loop.c"
	.globl	main
	.p2align	4, 0x90
	.type	main,@function
main:                                   # @main
# BB#0:
	push	ebp
	mov	ebp, esp
	sub	esp, 8
	mov	dword ptr [ebp - 4], 0
	mov	dword ptr [ebp - 8], 0
.LBB0_1:                                # =>This Inner Loop Header: Depth=1
	cmp	dword ptr [ebp - 8], 10
	jge	.LBB0_4
# BB#2:                                 #   in Loop: Header=BB0_1 Depth=1
	jmp	.LBB0_3
.LBB0_3:                                #   in Loop: Header=BB0_1 Depth=1
	mov	eax, dword ptr [ebp - 8]
	add	eax, 1
	mov	dword ptr [ebp - 8], eax
	jmp	.LBB0_1
.LBB0_4:
	mov	eax, dword ptr [ebp - 8]
	add	esp, 8
	pop	ebp
	ret
.Lfunc_end0:
	.size	main, .Lfunc_end0-main


	.ident	"Apple LLVM version 8.1.0 (clang-802.0.42)"
	.section	".note.GNU-stack","",@progbits
