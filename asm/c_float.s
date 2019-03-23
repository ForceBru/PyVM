; compile with `-m32 -mno-sse`

%include "startup.s"

LCPI0_0:
        dw   1082130432              ; float 4
main:                                   ; @main
        push    ebp
        mov     ebp, esp
        push    eax
        mov     dword [ebp - 4], 1088421888
        fld     dword [ebp - 4]
        fld     dword [LCPI0_0]
        fmulp   st1
        add     esp, 4
        pop     ebp
        ret