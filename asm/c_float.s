; compile with `-m32 -mno-sse`

%include "startup.s"

LCPI0_0:
        dd   1082130432              ; float 4
main:                                   ; @main
        push    ebp
        mov     ebp, esp
        sub     esp, 16
        mov     dword [ebp - 4], 0
        mov     dword [ebp - 8], 1088421888
        fld     dword [ebp - 8]
        fld     dword [LCPI0_0]
        fmulp   st1
        fnstcw  word [ebp - 14]
        mov     ax, word [ebp - 14]
        mov     word [ebp - 14], 3199
        fldcw   word [ebp - 14]
        mov     word [ebp - 14], ax
        fistp   dword [ebp - 12]
        fldcw   word [ebp - 14]
        mov     eax, dword [ebp - 12]
        add     esp, 16
        pop     ebp
        ret