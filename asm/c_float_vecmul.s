;float vecmul(float *v1, float* v2, int size) {
;    float ret = 0;
;
;    for(int i = 0; i < size; ++i) {
;        ret += v1[i] * v2[i];
;    }
;
;    return ret;
;}
;
;int main() {
;    float vec1[] = {1, 2, 3, 4, 5, 6};
;    float vec2[] = {6, 5, 4, 3, 2, 1};
;
;    float result = vecmul(vec1, vec2, 6);
;
;    return (int)result;
;}

%include "startup.s"

vecmul:                                 ; @vecmul
        push    ebp
        mov     ebp, esp
        sub     esp, 20
        mov     eax, dword [ebp + 16]
        mov     ecx, dword [ebp + 12]
        mov     edx, dword [ebp + 8]
        mov     dword [ebp - 4], 0
        mov     dword [ebp - 8], 0
        mov     dword [ebp - 12], eax ; 4-byte Spill
        mov     dword [ebp - 16], ecx ; 4-byte Spill
        mov     dword [ebp - 20], edx ; 4-byte Spill
LBB0_1:                                ; =>This Inner Loop Header: Depth=1
        mov     eax, dword [ebp - 8]
        cmp     eax, dword [ebp + 16]
        jge     LBB0_4
        mov     eax, dword [ebp + 8]
        mov     ecx, dword [ebp - 8]
        fld     dword [eax + 4*ecx]
        mov     eax, dword [ebp + 12]
        fld     dword [eax + 4*ecx]
        fmulp   st1, st0
        fld     dword [ebp - 4]
        faddp   st1, st0
        fstp    dword [ebp - 4]
        mov     eax, dword [ebp - 8]
        add     eax, 1
        mov     dword [ebp - 8], eax
        jmp     LBB0_1
LBB0_4:
        fld     dword [ebp - 4]
        add     esp, 20
        pop     ebp
        ret
main:                                   ; @main
        push    ebp
        mov     ebp, esp
        sub     esp, 88
        mov     dword [ebp - 4], 0
        mov     eax, dword [L__const.main.vec1+20]
        mov     dword [ebp - 8], eax
        mov     eax, dword [L__const.main.vec1+16]
        mov     dword [ebp - 12], eax
        mov     eax, dword [L__const.main.vec1+12]
        mov     dword [ebp - 16], eax
        mov     eax, dword [L__const.main.vec1+8]
        mov     dword [ebp - 20], eax
        mov     eax, dword [L__const.main.vec1+4]
        mov     dword [ebp - 24], eax
        mov     eax, dword [L__const.main.vec1]
        mov     dword [ebp - 28], eax
        mov     eax, dword [L__const.main.vec2+20]
        mov     dword [ebp - 32], eax
        mov     eax, dword [L__const.main.vec2+16]
        mov     dword [ebp - 36], eax
        mov     eax, dword [L__const.main.vec2+12]
        mov     dword [ebp - 40], eax
        mov     eax, dword [L__const.main.vec2+8]
        mov     dword [ebp - 44], eax
        mov     eax, dword [L__const.main.vec2+4]
        mov     dword [ebp - 48], eax
        mov     eax, dword [L__const.main.vec2]
        mov     dword [ebp - 52], eax
        mov     eax, esp
        lea     ecx, [ebp - 52]
        mov     dword [eax + 4], ecx
        lea     ecx, [ebp - 28]
        mov     dword [eax], ecx
        mov     dword [eax + 8], 6
        call    vecmul
        fstp    dword [ebp - 56]
        fld     dword [ebp - 56]
        fnstcw  word [ebp - 62]
        movzx   eax, word [ebp - 62]
        or      eax, 3072
        mov     dx, ax
        mov     word [ebp - 64], dx
        fldcw   word [ebp - 64]
        fistp   dword [ebp - 60]
        fldcw   word [ebp - 62]
        mov     eax, dword [ebp - 60]
        add     esp, 88
        pop     ebp
        ret
L__const.main.vec1:
        dd   1065353216              ; float 1
        dd   1073741824              ; float 2
        dd   1077936128              ; float 3
        dd   1082130432              ; float 4
        dd   1084227584              ; float 5
        dd   1086324736              ; float 6

L__const.main.vec2:
        dd   1086324736              ; float 6
        dd   1084227584              ; float 5
        dd   1082130432              ; float 4
        dd   1077936128              ; float 3
        dd   1073741824              ; float 2
        dd   1065353216              ; float 1