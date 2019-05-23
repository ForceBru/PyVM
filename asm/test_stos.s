USE32

STDOUT equ 1
SYS_EXIT equ 1
SYS_WRITE equ 4

%macro sys_write 3
      mov   eax, SYS_WRITE
      mov   ebx, %1
      mov   ecx, %2
      mov   edx, %3
      int   80h
%endmacro

section	.text
   global _start
   
_start:
    call main
    
exit:
    mov BYTE [retval], 48
    sys_write STDOUT, retval, 1
    mov ebx, 0
   
_exit:
    mov eax, SYS_EXIT
    int 0x80

%macro error 1
    mov ebx, %1
    jne _exit
%endmacro


%macro assert 2
%ifidni %1, stosb
    %assign size 1
%elifidni %1, stosd
    %assign size 4
%elifidni %1, stosw
    %assign size 2
%else
    %error "Invalid name"
%endif

mov eax, %2
lea edi, [buff]
mov ecx, bufsz / size
cld
rep %1

; eax holds 4 bytes of data that should've been stored
%if size = 1
    mov eax, (%2) + ((%2) << 8) + ((%2) << 16) + ((%2) << 24)
%elif size = 2
    mov eax, (%2) + ((%2) << 16)
%endif
    
lea edi, [buff]
%%loop:
    cmp DWORD [edi], eax
    error size
    add edi, 4
        
    cmp edi, buff + bufsz / 4
    jl %%loop
%endmacro
 
%assign NREP 16  
main:
    %assign i ((1<<8) - 1)
    %rep NREP
        assert stosb, i
    %assign i i - 1
    %if i < 0
        %exitrep
    %endif
    %endrep
    
    %assign i (1<<16) - 1
    %rep NREP
        assert stosw, i
    %assign i i-1
    %if i < 0
        %exitrep
    %endif
    %endrep
        
    %assign i (1<<8) + (NREP / 2)
    %rep NREP
        assert stosw, i
    %assign i i-1
    %if i < 0
        %exitrep
    %endif
    %endrep
        
    %assign i (1<<32) - 1
    %rep NREP
        assert stosd, i
    %assign i i-1
    %if i < 0
        %exitrep
    %endif
    %endrep
    
    %assign i (1<<16) + (NREP / 2)
    %rep NREP
        assert stosd, i
    %assign i i-1
    %if i < 0
        %exitrep
    %endif
    %endrep
    
    ret

section .data
   
segment .bss
    buff resb 256
    bufsz equ $ - buff
    retval resb 1
