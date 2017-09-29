	.text
	.intel_syntax noprefix
	.file	"pow.c"
	.globl	abs
	.p2align	4, 0x90
	.type	abs,@function
abs:                                    # @abs
# BB#0:
	mov	edx, dword ptr [esp + 8]
	mov	eax, dword ptr [esp + 4]
	mov	ecx, edx
	sar	ecx, 31
	add	eax, ecx
	adc	edx, ecx
	xor	eax, ecx
	xor	edx, ecx
	ret
.Lfunc_end0:
	.size	abs, .Lfunc_end0-abs

	.globl	pow
	.p2align	4, 0x90
	.type	pow,@function
pow:                                    # @pow
# BB#0:
	push	ebp
	push	ebx
	push	edi
	push	esi
	sub	esp, 16
	mov	edi, dword ptr [esp + 48]
	mov	ecx, -1
	mov	edx, -1
	test	edi, edi
	js	.LBB1_6
# BB#1:
	mov	eax, dword ptr [esp + 44]
	or	eax, edi
	je	.LBB1_2
# BB#3:
	mov	ecx, dword ptr [esp + 40]
	mov	ebp, dword ptr [esp + 36]
	mov	eax, ecx
	sar	eax, 31
	add	ebp, eax
	adc	ecx, eax
	xor	ebp, eax
	xor	ebx, ebx
	xor	ecx, eax
	mov	esi, ebp
	mov	eax, ebp
	mov	dword ptr [esp + 12], ebp # 4-byte Spill
	mul	ebp
	imul	esi, ecx
	mov	dword ptr [esp + 8], ecx # 4-byte Spill
	add	edx, esi
	mov	dword ptr [esp + 4], eax # 4-byte Spill
	mov	eax, ebp
	mov	ebp, ecx
	add	edx, esi
	xor	esi, esi
	mov	dword ptr [esp], edx    # 4-byte Spill
	.p2align	4, 0x90
.LBB1_4:                                # =>This Inner Loop Header: Depth=1
	mov	edx, edi
	mov	edi, dword ptr [esp + 12] # 4-byte Reload
	neg	edi
	mov	edi, 0
	sbb	edi, dword ptr [esp + 8] # 4-byte Folded Reload
	mov	edi, 0
	setl	cl
	and	cl, 1
	cmovne	edi, dword ptr [esp + 4] # 4-byte Folded Reload
	test	cl, cl
	mov	ecx, 0
	cmovne	ecx, dword ptr [esp]    # 4-byte Folded Reload
	add	eax, edi
	mov	edi, edx
	adc	ebp, ecx
	add	esi, 1
	adc	ebx, 0
	cmp	esi, dword ptr [esp + 44]
	mov	ecx, ebx
	sbb	ecx, edi
	jl	.LBB1_4
# BB#5:
	cmp	dword ptr [esp + 40], 0
	mov	ecx, dword ptr [esp + 44]
	setns	bl
	test	cl, 1
	mov	ecx, eax
	sete	bh
	xor	edx, edx
	neg	ecx
	sbb	edx, ebp
	or	bh, bl
	cmovne	edx, ebp
	cmovne	ecx, eax
	jmp	.LBB1_6
.LBB1_2:
	xor	edx, edx
	mov	ecx, 1
.LBB1_6:
	mov	eax, ecx
	add	esp, 16
	pop	esi
	pop	edi
	pop	ebx
	pop	ebp
	ret
.Lfunc_end1:
	.size	pow, .Lfunc_end1-pow

	.globl	main
	.p2align	4, 0x90
	.type	main,@function
main:                                   # @main
# BB#0:
	sub	esp, 12
	push	0
	push	4
	push	0
	push	5
	call	pow
	add	esp, 28
	ret
.Lfunc_end2:
	.size	main, .Lfunc_end2-main


	.ident	"Apple LLVM version 8.1.0 (clang-802.0.42)"
	.section	".note.GNU-stack","",@progbits
