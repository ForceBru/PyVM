;float sqrt(float S) {
;    float sqrt_s = S / 2;
;
;    for(int i = 0; i < 20; i++) {
;        sqrt_s = (sqrt_s + S/sqrt_s)/2;
;    }
;
;    return sqrt_s;
;}
;
;int main() {
;    double S = 268435456;
;
;    int root = sqrt(S);
;    if (root == 16384)
;        return 0;
;    return 1;
;}

%include "startup.s"


LCPI0_0:
        dd   1073741824              ; float 2
sqrt:                                   ; @sqrt
        push    ebp
        mov     ebp, esp
        sub     esp, 12
        fld     dword [ebp + 8]
        fld     dword [ebp + 8]
        fld     dword [LCPI0_0]
        fdivp   st1, st0
        fstp    dword [ebp - 4]
        mov     dword [ebp - 8], 0
        fstp    dword [ebp - 12]    ; 4-byte Folded Spill
LBB0_1:                                ; =>This Inner Loop Header: Depth=1
        cmp     dword [ebp - 8], 20
        jge     LBB0_4
        fld     dword [ebp - 4]
        fld     dword [ebp + 8]
        fdiv    st0, st1
        faddp   st1, st0
        fld     dword [LCPI0_0]
        fdivp   st1, st0
        fstp    dword [ebp - 4]
        mov     eax, dword [ebp - 8]
        add     eax, 1
        mov     dword [ebp - 8], eax
        jmp     LBB0_1
LBB0_4:
        fld     dword [ebp - 4]
        add     esp, 12
        pop     ebp
        ret
main:                                   ; @main
        push    ebp
        mov     ebp, esp
        sub     esp, 40
        mov     dword [ebp - 4], 0
        mov     dword [ebp - 12], 1102053376
        mov     dword [ebp - 16], 0
        fld     qword [ebp - 16]
        fstp    dword [ebp - 28]
        fld     dword [ebp - 28]
        mov     eax, esp
        fstp    dword [eax]
        call    sqrt
        fld     st0
        fnstcw  word [ebp - 30]
        movzx   eax, word [ebp - 30]
        or      eax, 3072
        mov     cx, ax
        mov     word [ebp - 32], cx
        fldcw   word [ebp - 32]
        fxch    st1
        fistp   dword [ebp - 24]
        fldcw   word [ebp - 30]
        mov     eax, dword [ebp - 24]
        mov     dword [ebp - 20], eax
        cmp     dword [ebp - 20], 16384
        fstp    dword [ebp - 36]    ; 4-byte Folded Spill
        jne     LBB1_2
        mov     dword [ebp - 4], 0
        jmp     LBB1_3
LBB1_2:
        mov     dword [ebp - 4], 1
LBB1_3:
        mov     eax, dword [ebp - 4]
        add     esp, 40
        pop     ebp
        ret