; compile with `-m32 -mno-sse`

; ACTUAL DAMN BABYLONIAN SQUARE ROOT!
;int main() {
;    double S = 268435456;
;    double sqrt_s = 8;
;
;    for(int i = 0; i < 20; i++) {
;        sqrt_s = (sqrt_s + S/sqrt_s)/2;
;    }
;
;    int root = sqrt_s;
;    if (root == 16384)
;        return 0;
;    return 1;
;}

%include "startup.s"


LCPI0_0:
        dd   1073741824              ; float 2
main:                                   ; @main
        push    ebp
        mov     ebp, esp
        sub     esp, 40
        mov     dword [ebp - 4], 0
        mov     dword [ebp - 12], 1102053376
        mov     dword [ebp - 16], 0
        mov     dword [ebp - 20], 1075838976
        mov     dword [ebp - 24], 0
        mov     dword [ebp - 28], 0
LBB0_1:                                ; =>This Inner Loop Header: Depth=1
        cmp     dword [ebp - 28], 20
        jge     LBB0_4
        fld     qword [ebp - 24]
        fld     qword [ebp - 16]
        fdiv    st0, st1
        faddp   st1, st0
        fld     dword [LCPI0_0]
        fdivp   st1, st0
        fstp    qword [ebp - 24]
        mov     eax, dword [ebp - 28]
        add     eax, 1
        mov     dword [ebp - 28], eax
        jmp     LBB0_1
LBB0_4:
        fld     qword [ebp - 24]
        fnstcw  word [ebp - 38]
        movzx   eax, word [ebp - 38]
        or      eax, 3072
        mov     cx, ax
        mov     word [ebp - 40], cx
        fldcw   word [ebp - 40]
        fistp   dword [ebp - 36]
        fldcw   word [ebp - 38]
        mov     eax, dword [ebp - 36]
        mov     dword [ebp - 32], eax
        cmp     dword [ebp - 32], 16384 ; the correct square root
        jne     LBB0_6
        mov     dword [ebp - 4], 0
        jmp     LBB0_7
LBB0_6:
        mov     dword [ebp - 4], 1
LBB0_7:
        mov     eax, dword [ebp - 4]
        add     esp, 40
        pop     ebp
        ret