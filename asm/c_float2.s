; compile with `-m32 -mno-sse`

;int main() {
;    float pi = 3.1415926;
;    float r = 4;
;
;    return pi * r;
;}

%include "startup.s"

main:                                   ; @main
        push    ebp
        mov     ebp, esp
        sub     esp, 20
        mov     dword [ebp - 4], 0
        mov     dword [ebp - 8], 1078530010
        mov     dword [ebp - 12], 1082130432
        fld     dword [ebp - 8]
        fld     dword [ebp - 12]
        fmulp   st1, st0
        fnstcw  word [ebp - 18]
        movzx   eax, word [ebp - 18]
        or      eax, 3072
        mov     cx, ax
        mov     word [ebp - 20], cx
        fldcw   word [ebp - 20]
        fistp   dword [ebp - 16]
        fldcw   word [ebp - 18]
        mov     eax, dword [ebp - 16]
        add     esp, 20
        pop     ebp
        ret