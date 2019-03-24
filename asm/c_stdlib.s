%include "definitions.h"
%include "startup.s"

; Compiled with `-nostdlib -m32 -mno-sse -O0`


strnlen:                                ; @strnlen
        push    ebp
        mov     ebp, esp
        sub     esp, 16
        mov     eax, dword [ebp + 12]
        mov     ecx, dword [ebp + 8]
        mov     edx, dword [ebp + 8]
        mov     dword [ebp - 4], edx
        mov     dword [ebp - 8], eax ; 4-byte Spill
        mov     dword [ebp - 12], ecx ; 4-byte Spill
LBB0_1:                                ; =>This Inner Loop Header: Depth=1
        xor     eax, eax
        mov     cl, al
        mov     eax, dword [ebp - 4]
        movsx   eax, byte [eax]
        cmp     eax, 0
        mov     byte [ebp - 13], cl ; 1-byte Spill
        je      LBB0_3
        cmp     dword [ebp + 12], 0
        setne   al
        mov     byte [ebp - 13], al ; 1-byte Spill
LBB0_3:                                ;   in Loop: Header=BB0_1 Depth=1
        mov     al, byte [ebp - 13] ; 1-byte Reload
        test    al, 1
        jne     LBB0_4
        jmp     LBB0_5
LBB0_4:                                ;   in Loop: Header=BB0_1 Depth=1
        mov     eax, dword [ebp - 4]
        add     eax, 1
        mov     dword [ebp - 4], eax
        mov     eax, dword [ebp + 12]
        add     eax, -1
        mov     dword [ebp + 12], eax
        jmp     LBB0_1
LBB0_5:
        mov     eax, dword [ebp - 4]
        mov     ecx, dword [ebp + 8]
        sub     eax, ecx
        add     esp, 16
        pop     ebp
        ret
strlen:                                 ; @strlen
        push    ebp
        mov     ebp, esp
        sub     esp, 8
        mov     eax, dword [ebp + 8]
        mov     ecx, dword [ebp + 8]
        mov     dword [ebp - 4], ecx
        mov     dword [ebp - 8], eax ; 4-byte Spill
LBB1_1:                                ; =>This Inner Loop Header: Depth=1
        mov     eax, dword [ebp - 4]
        movsx   eax, byte [eax]
        cmp     eax, 0
        je      LBB1_4
        jmp     LBB1_3
LBB1_3:                                ;   in Loop: Header=BB1_1 Depth=1
        mov     eax, dword [ebp - 4]
        add     eax, 1
        mov     dword [ebp - 4], eax
        jmp     LBB1_1
LBB1_4:
        mov     eax, dword [ebp - 4]
        mov     ecx, dword [ebp + 8]
        sub     eax, ecx
        add     esp, 8
        pop     ebp
        ret
puts:                                   ; @puts
        push    ebp
        mov     ebp, esp
        push    edi
        push    esi
        sub     esp, 32
        mov     eax, dword [ebp + 8]
        xor     ecx, ecx
        mov     edx, dword [ebp + 8]
        mov     esi, dword [ebp + 8]
        mov     edi, esp
        mov     dword [edi], esi
        mov     dword [ebp - 12], eax ; 4-byte Spill
        mov     dword [ebp - 16], ecx ; 4-byte Spill
        mov     dword [ebp - 20], edx ; 4-byte Spill
        call    strlen
        mov     dword [esp], STDOUT
        mov     ecx, dword [ebp - 20] ; 4-byte Reload
        mov     dword [esp + 4], ecx
        mov     dword [esp + 8], eax
        call    sys_write
        add     esp, 32
        pop     esi
        pop     edi
        pop     ebp
        ret
vsprintf:                               ; @vsprintf
        push    ebp
        mov     ebp, esp
        push    ebx
        push    edi
        push    esi
        sub     esp, 108
        mov     eax, dword [ebp + 16]
        mov     ecx, dword [ebp + 12]
        mov     edx, dword [ebp + 8]
        mov     esi, dword [ebp + 8]
        mov     dword [ebp - 32], esi
        mov     dword [ebp - 64], eax ; 4-byte Spill
        mov     dword [ebp - 68], ecx ; 4-byte Spill
        mov     dword [ebp - 72], edx ; 4-byte Spill
LBB3_1:                                ; =>This Loop Header: Depth=1
        mov     eax, dword [ebp + 12]
        cmp     byte [eax], 0
        je      LBB3_84
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        cmp     eax, 37
        je      LBB3_4
        mov     eax, dword [ebp + 12]
        mov     cl, byte [eax]
        mov     eax, dword [ebp - 32]
        mov     edx, eax
        add     edx, 1
        mov     dword [ebp - 32], edx
        mov     byte [eax], cl
        jmp     LBB3_83
LBB3_4:                                ;   in Loop: Header=BB3_1 Depth=1
        mov     dword [ebp - 40], 0
LBB3_5:                                ;   Parent Loop BB3_1 Depth=1
        mov     eax, dword [ebp + 12]
        inc     eax
        mov     dword [ebp + 12], eax
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        add     eax, -32
        mov     ecx, eax
        sub     ecx, 16
        mov     dword [ebp - 76], eax ; 4-byte Spill
        mov     dword [ebp - 80], ecx ; 4-byte Spill
        ja      LBB3_11
        mov     eax, dword [ebp - 76] ; 4-byte Reload
        mov     ecx, dword [4*eax + LJTI3_0]
        jmp     ecx
LBB3_6:                                ;   in Loop: Header=BB3_5 Depth=2
        mov     eax, dword [ebp - 40]
        or      eax, 16
        mov     dword [ebp - 40], eax
        jmp     LBB3_5
LBB3_7:                                ;   in Loop: Header=BB3_5 Depth=2
        mov     eax, dword [ebp - 40]
        or      eax, 4
        mov     dword [ebp - 40], eax
        jmp     LBB3_5
LBB3_8:                                ;   in Loop: Header=BB3_5 Depth=2
        mov     eax, dword [ebp - 40]
        or      eax, 8
        mov     dword [ebp - 40], eax
        jmp     LBB3_5
LBB3_9:                                ;   in Loop: Header=BB3_5 Depth=2
        mov     eax, dword [ebp - 40]
        or      eax, 64
        mov     dword [ebp - 40], eax
        jmp     LBB3_5
LBB3_10:                               ;   in Loop: Header=BB3_5 Depth=2
        mov     eax, dword [ebp - 40]
        or      eax, 1
        mov     dword [ebp - 40], eax
        jmp     LBB3_5
LBB3_11:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     dword [ebp - 44], -1
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        mov     dword [esp], eax
        call    isdigit
        cmp     eax, 0
        je      LBB3_13
        lea     eax, [ebp + 12]
        mov     dword [esp], eax
        call    skip_atoi
        mov     dword [ebp - 44], eax
        jmp     LBB3_18
LBB3_13:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        cmp     eax, 42
        jne     LBB3_17
        mov     eax, dword [ebp + 12]
        add     eax, 1
        mov     dword [ebp + 12], eax
        mov     eax, dword [ebp + 16]
        mov     ecx, eax
        add     ecx, 4
        mov     dword [ebp + 16], ecx
        mov     eax, dword [eax]
        mov     dword [ebp - 44], eax
        cmp     dword [ebp - 44], 0
        jge     LBB3_16
        xor     eax, eax
        sub     eax, dword [ebp - 44]
        mov     dword [ebp - 44], eax
        mov     eax, dword [ebp - 40]
        or      eax, 16
        mov     dword [ebp - 40], eax
LBB3_16:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_17
LBB3_17:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_18
LBB3_18:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     dword [ebp - 48], -1
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        cmp     eax, 46
        jne     LBB3_27
        mov     eax, dword [ebp + 12]
        add     eax, 1
        mov     dword [ebp + 12], eax
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        mov     dword [esp], eax
        call    isdigit
        cmp     eax, 0
        je      LBB3_21
        lea     eax, [ebp + 12]
        mov     dword [esp], eax
        call    skip_atoi
        mov     dword [ebp - 48], eax
        jmp     LBB3_24
LBB3_21:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        cmp     eax, 42
        jne     LBB3_23
        mov     eax, dword [ebp + 12]
        add     eax, 1
        mov     dword [ebp + 12], eax
        mov     eax, dword [ebp + 16]
        mov     ecx, eax
        add     ecx, 4
        mov     dword [ebp + 16], ecx
        mov     eax, dword [eax]
        mov     dword [ebp - 48], eax
LBB3_23:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_24
LBB3_24:                               ;   in Loop: Header=BB3_1 Depth=1
        cmp     dword [ebp - 48], 0
        jge     LBB3_26
        mov     dword [ebp - 48], 0
LBB3_26:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_27
LBB3_27:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     dword [ebp - 52], -1
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        cmp     eax, 104
        je      LBB3_30
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        cmp     eax, 108
        je      LBB3_30
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        cmp     eax, 76
        jne     LBB3_31
LBB3_30:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        mov     dword [ebp - 52], eax
        mov     eax, dword [ebp + 12]
        add     eax, 1
        mov     dword [ebp + 12], eax
LBB3_31:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     dword [ebp - 28], 10
        mov     eax, dword [ebp + 12]
        movsx   eax, byte [eax]
        add     eax, -37
        mov     ecx, eax
        sub     ecx, 83
        mov     dword [ebp - 84], eax ; 4-byte Spill
        mov     dword [ebp - 88], ecx ; 4-byte Spill
        ja      LBB3_67
        mov     eax, dword [ebp - 84] ; 4-byte Reload
        mov     ecx, dword [4*eax + LJTI3_1]
        jmp     ecx
LBB3_32:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp - 40]
        and     eax, 16
        cmp     eax, 0
        jne     LBB3_37
        jmp     LBB3_34
LBB3_34:                               ;   Parent Loop BB3_1 Depth=1
        mov     eax, dword [ebp - 44]
        add     eax, -1
        mov     dword [ebp - 44], eax
        cmp     eax, 0
        jle     LBB3_36
        mov     eax, dword [ebp - 32]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp - 32], ecx
        mov     byte [eax], 32
        jmp     LBB3_34
LBB3_36:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_37
LBB3_37:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp + 16]
        mov     ecx, eax
        add     ecx, 4
        mov     dword [ebp + 16], ecx
        mov     eax, dword [eax]
        mov     dl, al
        mov     eax, dword [ebp - 32]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp - 32], ecx
        mov     byte [eax], dl
LBB3_38:                               ;   Parent Loop BB3_1 Depth=1
        mov     eax, dword [ebp - 44]
        add     eax, -1
        mov     dword [ebp - 44], eax
        cmp     eax, 0
        jle     LBB3_40
        mov     eax, dword [ebp - 32]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp - 32], ecx
        mov     byte [eax], 32
        jmp     LBB3_38
LBB3_40:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_83
LBB3_41:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp + 16]
        mov     ecx, eax
        add     ecx, 4
        mov     dword [ebp + 16], ecx
        mov     eax, dword [eax]
        mov     dword [ebp - 36], eax
        mov     eax, dword [ebp - 36]
        mov     ecx, dword [ebp - 48]
        mov     edx, esp
        mov     dword [edx + 4], ecx
        mov     dword [edx], eax
        call    strnlen
        mov     dword [ebp - 16], eax
        mov     eax, dword [ebp - 40]
        and     eax, 16
        cmp     eax, 0
        jne     LBB3_46
        jmp     LBB3_43
LBB3_43:                               ;   Parent Loop BB3_1 Depth=1
        mov     eax, dword [ebp - 16]
        mov     ecx, dword [ebp - 44]
        mov     edx, ecx
        add     edx, -1
        mov     dword [ebp - 44], edx
        cmp     eax, ecx
        jge     LBB3_45
        mov     eax, dword [ebp - 32]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp - 32], ecx
        mov     byte [eax], 32
        jmp     LBB3_43
LBB3_45:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_46
LBB3_46:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     dword [ebp - 24], 0
LBB3_47:                               ;   Parent Loop BB3_1 Depth=1
        mov     eax, dword [ebp - 24]
        cmp     eax, dword [ebp - 16]
        jge     LBB3_50
        mov     eax, dword [ebp - 36]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp - 36], ecx
        mov     dl, byte [eax]
        mov     eax, dword [ebp - 32]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp - 32], ecx
        mov     byte [eax], dl
        mov     eax, dword [ebp - 24]
        add     eax, 1
        mov     dword [ebp - 24], eax
        jmp     LBB3_47
LBB3_50:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_51
LBB3_51:                               ;   Parent Loop BB3_1 Depth=1
        mov     eax, dword [ebp - 16]
        mov     ecx, dword [ebp - 44]
        mov     edx, ecx
        add     edx, -1
        mov     dword [ebp - 44], edx
        cmp     eax, ecx
        jge     LBB3_53
        mov     eax, dword [ebp - 32]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp - 32], ecx
        mov     byte [eax], 32
        jmp     LBB3_51
LBB3_53:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_83
LBB3_54:                               ;   in Loop: Header=BB3_1 Depth=1
        cmp     dword [ebp - 44], -1
        jne     LBB3_56
        mov     dword [ebp - 44], 8
        mov     eax, dword [ebp - 40]
        or      eax, 1
        mov     dword [ebp - 40], eax
LBB3_56:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp - 32]
        mov     ecx, dword [ebp + 16]
        mov     edx, ecx
        add     edx, 4
        mov     dword [ebp + 16], edx
        mov     ecx, dword [ecx]
        mov     edx, dword [ebp - 44]
        mov     esi, dword [ebp - 48]
        mov     edi, dword [ebp - 40]
        mov     dword [esp], eax
        mov     dword [esp + 4], ecx
        mov     dword [esp + 8], 16
        mov     dword [esp + 12], edx
        mov     dword [esp + 16], esi
        mov     dword [esp + 20], edi
        call    number
        mov     dword [ebp - 32], eax
        jmp     LBB3_83
LBB3_57:                               ;   in Loop: Header=BB3_1 Depth=1
        cmp     dword [ebp - 52], 108
        jne     LBB3_59
        mov     eax, dword [ebp + 16]
        mov     ecx, eax
        add     ecx, 4
        mov     dword [ebp + 16], ecx
        mov     eax, dword [eax]
        mov     dword [ebp - 56], eax
        mov     eax, dword [ebp - 32]
        mov     ecx, dword [ebp + 8]
        sub     eax, ecx
        mov     ecx, dword [ebp - 56]
        mov     dword [ecx], eax
        jmp     LBB3_60
LBB3_59:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp + 16]
        mov     ecx, eax
        add     ecx, 4
        mov     dword [ebp + 16], ecx
        mov     eax, dword [eax]
        mov     dword [ebp - 60], eax
        mov     eax, dword [ebp - 32]
        mov     ecx, dword [ebp + 8]
        sub     eax, ecx
        mov     ecx, dword [ebp - 60]
        mov     dword [ecx], eax
LBB3_60:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_83
LBB3_61:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp - 32]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp - 32], ecx
        mov     byte [eax], 37
        jmp     LBB3_83
LBB3_62:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     dword [ebp - 28], 8
        jmp     LBB3_71
LBB3_63:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp - 40]
        or      eax, 32
        mov     dword [ebp - 40], eax
LBB3_64:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     dword [ebp - 28], 16
        jmp     LBB3_71
LBB3_65:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp - 40]
        or      eax, 2
        mov     dword [ebp - 40], eax
LBB3_66:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_71
LBB3_67:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp - 32]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp - 32], ecx
        mov     byte [eax], 37
        mov     eax, dword [ebp + 12]
        cmp     byte [eax], 0
        je      LBB3_69
        mov     eax, dword [ebp + 12]
        mov     cl, byte [eax]
        mov     eax, dword [ebp - 32]
        mov     edx, eax
        add     edx, 1
        mov     dword [ebp - 32], edx
        mov     byte [eax], cl
        jmp     LBB3_70
LBB3_69:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp + 12]
        add     eax, -1
        mov     dword [ebp + 12], eax
LBB3_70:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_83
LBB3_71:                               ;   in Loop: Header=BB3_1 Depth=1
        cmp     dword [ebp - 52], 108
        jne     LBB3_73
        mov     eax, dword [ebp + 16]
        mov     ecx, eax
        add     ecx, 4
        mov     dword [ebp + 16], ecx
        mov     eax, dword [eax]
        mov     dword [ebp - 20], eax
        jmp     LBB3_82
LBB3_73:                               ;   in Loop: Header=BB3_1 Depth=1
        cmp     dword [ebp - 52], 104
        jne     LBB3_77
        mov     eax, dword [ebp + 16]
        mov     ecx, eax
        add     ecx, 4
        mov     dword [ebp + 16], ecx
        mov     eax, dword [eax]
        mov     dx, ax
        movzx   eax, dx
        mov     dword [ebp - 20], eax
        mov     eax, dword [ebp - 40]
        and     eax, 2
        cmp     eax, 0
        je      LBB3_76
        mov     eax, dword [ebp - 20]
        mov     cx, ax
        movsx   eax, cx
        mov     dword [ebp - 20], eax
LBB3_76:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_81
LBB3_77:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp - 40]
        and     eax, 2
        cmp     eax, 0
        je      LBB3_79
        mov     eax, dword [ebp + 16]
        mov     ecx, eax
        add     ecx, 4
        mov     dword [ebp + 16], ecx
        mov     eax, dword [eax]
        mov     dword [ebp - 20], eax
        jmp     LBB3_80
LBB3_79:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp + 16]
        mov     ecx, eax
        add     ecx, 4
        mov     dword [ebp + 16], ecx
        mov     eax, dword [eax]
        mov     dword [ebp - 20], eax
LBB3_80:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_81
LBB3_81:                               ;   in Loop: Header=BB3_1 Depth=1
        jmp     LBB3_82
LBB3_82:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp - 32]
        mov     ecx, dword [ebp - 20]
        mov     edx, dword [ebp - 28]
        mov     esi, dword [ebp - 44]
        mov     edi, dword [ebp - 48]
        mov     ebx, dword [ebp - 40]
        mov     dword [esp], eax
        mov     dword [esp + 4], ecx
        mov     dword [esp + 8], edx
        mov     dword [esp + 12], esi
        mov     dword [esp + 16], edi
        mov     dword [esp + 20], ebx
        call    number
        mov     dword [ebp - 32], eax
LBB3_83:                               ;   in Loop: Header=BB3_1 Depth=1
        mov     eax, dword [ebp + 12]
        add     eax, 1
        mov     dword [ebp + 12], eax
        jmp     LBB3_1
LBB3_84:
        mov     eax, dword [ebp - 32]
        mov     byte [eax], 0
        mov     eax, dword [ebp - 32]
        mov     ecx, dword [ebp + 8]
        sub     eax, ecx
        add     esp, 108
        pop     esi
        pop     edi
        pop     ebx
        pop     ebp
        ret
LJTI3_0:
        dd   LBB3_8
        dd   LBB3_11
        dd   LBB3_11
        dd   LBB3_9
        dd   LBB3_11
        dd   LBB3_11
        dd   LBB3_11
        dd   LBB3_11
        dd   LBB3_11
        dd   LBB3_11
        dd   LBB3_11
        dd   LBB3_7
        dd   LBB3_11
        dd   LBB3_6
        dd   LBB3_11
        dd   LBB3_11
        dd   LBB3_10
LJTI3_1:
        dd   LBB3_61
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_64
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_32
        dd   LBB3_65
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_65
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_57
        dd   LBB3_62
        dd   LBB3_54
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_41
        dd   LBB3_67
        dd   LBB3_66
        dd   LBB3_67
        dd   LBB3_67
        dd   LBB3_63
isdigit:                                ; @isdigit
        push    ebp
        mov     ebp, esp
        sub     esp, 8
        mov     eax, dword [ebp + 8]
        xor     ecx, ecx
        mov     dl, cl
        cmp     dword [ebp + 8], 48
        mov     dword [ebp - 4], eax ; 4-byte Spill
        mov     byte [ebp - 5], dl  ; 1-byte Spill
        jl      LBB4_2
        cmp     dword [ebp + 8], 57
        setle   al
        mov     byte [ebp - 5], al  ; 1-byte Spill
LBB4_2:
        mov     al, byte [ebp - 5]  ; 1-byte Reload
        and     al, 1
        movzx   eax, al
        add     esp, 8
        pop     ebp
        ret
skip_atoi:                              ; @skip_atoi
        push    ebp
        mov     ebp, esp
        push    esi
        sub     esp, 20
        mov     eax, dword [ebp + 8]
        mov     dword [ebp - 8], 0
        mov     dword [ebp - 12], eax ; 4-byte Spill
LBB5_1:                                ; =>This Inner Loop Header: Depth=1
        mov     eax, dword [ebp + 8]
        mov     eax, dword [eax]
        movsx   eax, byte [eax]
        mov     dword [esp], eax
        call    isdigit
        cmp     eax, 0
        je      LBB5_3
        imul    eax, dword [ebp - 8], 10
        mov     ecx, dword [ebp + 8]
        mov     edx, dword [ecx]
        mov     esi, edx
        add     esi, 1
        mov     dword [ecx], esi
        movsx   ecx, byte [edx]
        add     eax, ecx
        sub     eax, 48
        mov     dword [ebp - 8], eax
        jmp     LBB5_1
LBB5_3:
        mov     eax, dword [ebp - 8]
        add     esp, 20
        pop     esi
        pop     ebp
        ret
number:                                 ; @number
        push    ebp
        mov     ebp, esp
        push    ebx
        push    edi
        push    esi
        sub     esp, 112
        mov     eax, dword [ebp + 28]
        mov     ecx, dword [ebp + 24]
        mov     edx, dword [ebp + 20]
        mov     esi, dword [ebp + 16]
        mov     edi, dword [ebp + 12]
        mov     ebx, dword [ebp + 8]
        mov     dword [ebp - 104], eax ; 4-byte Spill
        mov     eax, dword [ebp + 28]
        and     eax, 32
        mov     byte [ebp - 85], al
        mov     eax, dword [ebp + 28]
        and     eax, 16
        cmp     eax, 0
        mov     dword [ebp - 108], ecx ; 4-byte Spill
        mov     dword [ebp - 112], edx ; 4-byte Spill
        mov     dword [ebp - 116], esi ; 4-byte Spill
        mov     dword [ebp - 120], edi ; 4-byte Spill
        mov     dword [ebp - 124], ebx ; 4-byte Spill
        je      LBB6_2
        mov     eax, dword [ebp + 28]
        and     eax, -2
        mov     dword [ebp + 28], eax
LBB6_2:
        cmp     dword [ebp + 16], 2
        jl      LBB6_4
        cmp     dword [ebp + 16], 16
        jle     LBB6_5
LBB6_4:
        mov     dword [ebp - 16], 0
        jmp     LBB6_59
LBB6_5:
        mov     eax, dword [ebp + 28]
        and     eax, 1
        cmp     eax, 0
        mov     eax, 48
        mov     ecx, 32
        cmovne  ecx, eax
        mov     dl, cl
        mov     byte [ebp - 83], dl
        mov     byte [ebp - 84], 0
        mov     eax, dword [ebp + 28]
        and     eax, 2
        cmp     eax, 0
        je      LBB6_15
        cmp     dword [ebp + 12], 0
        jge     LBB6_8
        xor     eax, eax
        mov     byte [ebp - 84], 45
        sub     eax, dword [ebp + 12]
        mov     dword [ebp + 12], eax
        mov     eax, dword [ebp + 20]
        add     eax, -1
        mov     dword [ebp + 20], eax
        jmp     LBB6_14
LBB6_8:
        mov     eax, dword [ebp + 28]
        and     eax, 4
        cmp     eax, 0
        je      LBB6_10
        mov     byte [ebp - 84], 43
        mov     eax, dword [ebp + 20]
        add     eax, -1
        mov     dword [ebp + 20], eax
        jmp     LBB6_13
LBB6_10:
        mov     eax, dword [ebp + 28]
        and     eax, 8
        cmp     eax, 0
        je      LBB6_12
        mov     byte [ebp - 84], 32
        mov     eax, dword [ebp + 20]
        add     eax, -1
        mov     dword [ebp + 20], eax
LBB6_12:
        jmp     LBB6_13
LBB6_13:
        jmp     LBB6_14
LBB6_14:
        jmp     LBB6_15
LBB6_15:
        mov     eax, dword [ebp + 28]
        and     eax, 64
        cmp     eax, 0
        je      LBB6_22
        cmp     dword [ebp + 16], 16
        jne     LBB6_18
        mov     eax, dword [ebp + 20]
        sub     eax, 2
        mov     dword [ebp + 20], eax
        jmp     LBB6_21
LBB6_18:
        cmp     dword [ebp + 16], 8
        jne     LBB6_20
        mov     eax, dword [ebp + 20]
        add     eax, -1
        mov     dword [ebp + 20], eax
LBB6_20:
        jmp     LBB6_21
LBB6_21:
        jmp     LBB6_22
LBB6_22:
        mov     dword [ebp - 92], 0
        cmp     dword [ebp + 12], 0
        jne     LBB6_24
        mov     eax, dword [ebp - 92]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp - 92], ecx
        mov     byte [ebp + eax - 82], 48
        jmp     LBB6_28
LBB6_24:
        jmp     LBB6_25
LBB6_25:                               ; =>This Inner Loop Header: Depth=1
        cmp     dword [ebp + 12], 0
        je      LBB6_27
        mov     eax, dword [ebp + 12]
        xor     edx, edx
        div     dword [ebp + 16]
        mov     dword [ebp - 96], edx
        mov     ecx, dword [ebp + 12]
        mov     eax, ecx
        xor     edx, edx
        div     dword [ebp + 16]
        mov     dword [ebp + 12], eax
        mov     eax, dword [ebp - 96]
        mov     dword [ebp - 100], eax
        mov     eax, dword [ebp - 100]
        movsx   eax, byte [eax + number.digits]
        movsx   ecx, byte [ebp - 85]
        or      eax, ecx
        mov     bl, al
        mov     eax, dword [ebp - 92]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp - 92], ecx
        mov     byte [ebp + eax - 82], bl
        jmp     LBB6_25
LBB6_27:
        jmp     LBB6_28
LBB6_28:
        mov     eax, dword [ebp - 92]
        cmp     eax, dword [ebp + 24]
        jle     LBB6_30
        mov     eax, dword [ebp - 92]
        mov     dword [ebp + 24], eax
LBB6_30:
        mov     eax, dword [ebp + 24]
        mov     ecx, dword [ebp + 20]
        sub     ecx, eax
        mov     dword [ebp + 20], ecx
        mov     eax, dword [ebp + 28]
        and     eax, 17
        cmp     eax, 0
        jne     LBB6_35
        jmp     LBB6_32
LBB6_32:                               ; =>This Inner Loop Header: Depth=1
        mov     eax, dword [ebp + 20]
        mov     ecx, eax
        add     ecx, -1
        mov     dword [ebp + 20], ecx
        cmp     eax, 0
        jle     LBB6_34
        mov     eax, dword [ebp + 8]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp + 8], ecx
        mov     byte [eax], 32
        jmp     LBB6_32
LBB6_34:
        jmp     LBB6_35
LBB6_35:
        cmp     byte [ebp - 84], 0
        je      LBB6_37
        mov     al, byte [ebp - 84]
        mov     ecx, dword [ebp + 8]
        mov     edx, ecx
        add     edx, 1
        mov     dword [ebp + 8], edx
        mov     byte [ecx], al
LBB6_37:
        mov     eax, dword [ebp + 28]
        and     eax, 64
        cmp     eax, 0
        je      LBB6_44
        cmp     dword [ebp + 16], 8
        jne     LBB6_40
        mov     eax, dword [ebp + 8]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp + 8], ecx
        mov     byte [eax], 48
        jmp     LBB6_43
LBB6_40:
        cmp     dword [ebp + 16], 16
        jne     LBB6_42
        mov     eax, dword [ebp + 8]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp + 8], ecx
        mov     byte [eax], 48
        movsx   eax, byte [ebp - 85]
        or      eax, 88
        mov     dl, al
        mov     eax, dword [ebp + 8]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp + 8], ecx
        mov     byte [eax], dl
LBB6_42:
        jmp     LBB6_43
LBB6_43:
        jmp     LBB6_44
LBB6_44:
        mov     eax, dword [ebp + 28]
        and     eax, 16
        cmp     eax, 0
        jne     LBB6_49
        jmp     LBB6_46
LBB6_46:                               ; =>This Inner Loop Header: Depth=1
        mov     eax, dword [ebp + 20]
        mov     ecx, eax
        add     ecx, -1
        mov     dword [ebp + 20], ecx
        cmp     eax, 0
        jle     LBB6_48
        mov     al, byte [ebp - 83]
        mov     ecx, dword [ebp + 8]
        mov     edx, ecx
        add     edx, 1
        mov     dword [ebp + 8], edx
        mov     byte [ecx], al
        jmp     LBB6_46
LBB6_48:
        jmp     LBB6_49
LBB6_49:
        jmp     LBB6_50
LBB6_50:                               ; =>This Inner Loop Header: Depth=1
        mov     eax, dword [ebp - 92]
        mov     ecx, dword [ebp + 24]
        mov     edx, ecx
        add     edx, -1
        mov     dword [ebp + 24], edx
        cmp     eax, ecx
        jge     LBB6_52
        mov     eax, dword [ebp + 8]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp + 8], ecx
        mov     byte [eax], 48
        jmp     LBB6_50
LBB6_52:
        jmp     LBB6_53
LBB6_53:                               ; =>This Inner Loop Header: Depth=1
        mov     eax, dword [ebp - 92]
        mov     ecx, eax
        add     ecx, -1
        mov     dword [ebp - 92], ecx
        cmp     eax, 0
        jle     LBB6_55
        mov     eax, dword [ebp - 92]
        mov     cl, byte [ebp + eax - 82]
        mov     eax, dword [ebp + 8]
        mov     edx, eax
        add     edx, 1
        mov     dword [ebp + 8], edx
        mov     byte [eax], cl
        jmp     LBB6_53
LBB6_55:
        jmp     LBB6_56
LBB6_56:                               ; =>This Inner Loop Header: Depth=1
        mov     eax, dword [ebp + 20]
        mov     ecx, eax
        add     ecx, -1
        mov     dword [ebp + 20], ecx
        cmp     eax, 0
        jle     LBB6_58
        mov     eax, dword [ebp + 8]
        mov     ecx, eax
        add     ecx, 1
        mov     dword [ebp + 8], ecx
        mov     byte [eax], 32
        jmp     LBB6_56
LBB6_58:
        mov     eax, dword [ebp + 8]
        mov     dword [ebp - 16], eax
LBB6_59:
        mov     eax, dword [ebp - 16]
        add     esp, 112
        pop     esi
        pop     edi
        pop     ebx
        pop     ebp
        ret
sprintf:                                ; @sprintf
        push    ebp
        mov     ebp, esp
        push    ebx
        push    edi
        push    esi
        sub     esp, 28
        mov     eax, dword [ebp + 12]
        mov     ecx, dword [ebp + 8]
        lea     edx, [ebp + 16]
        mov     dword [ebp - 16], edx
        mov     edx, dword [ebp + 8]
        mov     esi, dword [ebp + 12]
        mov     edi, dword [ebp - 16]
        mov     ebx, esp
        mov     dword [ebx + 8], edi
        mov     dword [ebx + 4], esi
        mov     dword [ebx], edx
        mov     dword [ebp - 24], eax ; 4-byte Spill
        mov     dword [ebp - 28], ecx ; 4-byte Spill
        call    vsprintf
        mov     dword [ebp - 20], eax
        mov     eax, dword [ebp - 20]
        add     esp, 28
        pop     esi
        pop     edi
        pop     ebx
        pop     ebp
        ret
printf:                                 ; @printf
        push    ebp
        mov     ebp, esp
        push    esi
        sub     esp, 1060
        mov     eax, dword [ebp + 8]
        lea     ecx, [ebp + 12]
        mov     dword [ebp - 1032], ecx
        mov     ecx, dword [ebp + 8]
        mov     edx, dword [ebp - 1032]
        mov     esi, esp
        mov     dword [esi + 8], edx
        mov     dword [esi + 4], ecx
        lea     ecx, [ebp - 1028]
        mov     dword [esi], ecx
        mov     dword [ebp - 1040], eax ; 4-byte Spill
        mov     dword [ebp - 1044], ecx ; 4-byte Spill
        call    vsprintf
        mov     dword [ebp - 1036], eax
        mov     eax, esp
        mov     ecx, dword [ebp - 1044] ; 4-byte Reload
        mov     dword [eax], ecx
        call    puts
        mov     ecx, dword [ebp - 1036]
        mov     dword [ebp - 1048], eax ; 4-byte Spill
        mov     eax, ecx
        add     esp, 1060
        pop     esi
        pop     ebp
        ret
main:                                   ; @main
        push    ebp
        mov     ebp, esp
        sub     esp, 24
        mov     dword [ebp - 4], 0
        lea     eax, [L.str]
        mov     dword [esp], eax
        call    printf
        xor     ecx, ecx
        mov     dword [ebp - 8], eax ; 4-byte Spill
        mov     eax, ecx
        add     esp, 24
        pop     ebp
        ret
L.str:
        db  "Hello, world!", 10, 0

number.digits:
        db  "0123456789ABCDEF"