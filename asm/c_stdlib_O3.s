%include "startup.s"

memset:                                 ; @memset
        push    esi
        mov     ecx, dword  [esp + 16]
        mov     eax, dword  [esp + 8]
        test    ecx, ecx
        je      LBB0_3
        mov     edx, dword  [esp + 12]
        mov     esi, eax
LBB0_2:                                ; =>This Inner Loop Header: Depth=1
        mov     byte  [esi], dl
        inc     esi
        dec     ecx
        jne     LBB0_2
LBB0_3:
        pop     esi
        ret
strnlen:                                ; @strnlen
        push    ebx
        push    esi
        mov     edx, dword  [esp + 16]
        mov     ecx, dword  [esp + 12]
        test    edx, edx
        mov     eax, ecx
        je      LBB1_5
        mov     al, byte  [ecx]
        test    al, al
        mov     eax, ecx
        je      LBB1_5
        dec     edx
        mov     esi, ecx
LBB1_3:                                ; =>This Inner Loop Header: Depth=1
        lea     eax, [esi + 1]
        add     edx, -1
        jae     LBB1_5
        movzx   ebx, byte  [esi + 1]
        mov     esi, eax
        test    bl, bl
        jne     LBB1_3
LBB1_5:
        sub     eax, ecx
        pop     esi
        pop     ebx
        ret
strlen:                                 ; @strlen
        mov     ecx, dword  [esp + 4]
        lea     eax, [ecx - 1]
LBB2_1:                                ; =>This Inner Loop Header: Depth=1
        cmp     byte  [eax + 1], 0
        lea     eax, [eax + 1]
        jne     LBB2_1
        sub     eax, ecx
        ret
puts:                                   ; @puts
        sub     esp, 12
        mov     eax, dword  [esp + 16]
        lea     ecx, [eax - 1]
LBB3_1:                                ; =>This Inner Loop Header: Depth=1
        cmp     byte  [ecx + 1], 0
        lea     ecx, [ecx + 1]
        jne     LBB3_1
        sub     ecx, eax
        sub     esp, 4
        push    ecx
        push    eax
        push    0
        call    sys_write
        add     esp, 28
        ret
vsprintf:                               ; @vsprintf
        push    ebp
        push    ebx
        push    edi
        push    esi
        sub     esp, 12
        mov     eax, dword  [esp + 40]
        mov     ebp, dword  [esp + 36]
        mov     esi, dword  [esp + 32]
        mov     dword  [esp], eax    ; 4-byte Spill
        mov     al, byte  [ebp]
        cmp     al, 37
        je      LBB4_3
LBB4_2:
        test    al, al
        je      LBB4_77
        mov     byte  [esi], al
LBB4_75:
        inc     esi
        inc     ebp
        mov     al, byte  [ebp]
        cmp     al, 37
        jne     LBB4_2
        jmp     LBB4_3
LBB4_4:                                ;   in Loop: Header=BB4_5 Depth=2
        or      eax, edx
        inc     ebp
LBB4_5:                                ;   Parent Loop BB4_3 Depth=1
        movzx   ecx, byte  [ebp]
        movsx   edi, cl
        lea     ebx, [edi - 32]
        cmp     ebx, 16
        ja      LBB4_11
        mov     edx, 4
        jmp     dword  [4*ebx + LJTI4_0]
LBB4_7:                                ;   in Loop: Header=BB4_5 Depth=2
        mov     edx, 8
        jmp     LBB4_4
LBB4_8:                                ;   in Loop: Header=BB4_5 Depth=2
        mov     edx, 64
        jmp     LBB4_4
LBB4_9:                                ;   in Loop: Header=BB4_5 Depth=2
        mov     edx, 16
        jmp     LBB4_4
LBB4_10:                               ;   in Loop: Header=BB4_5 Depth=2
        mov     edx, 1
        jmp     LBB4_4
LBB4_11:                               ;   in Loop: Header=BB4_3 Depth=1
        add     edi, -48
        cmp     edi, 9
        jbe     LBB4_16
        mov     edi, -1
        cmp     cl, 42
        jne     LBB4_15
        mov     ecx, dword  [esp]    ; 4-byte Reload
        inc     ebp
        mov     edi, dword  [ecx]
        add     ecx, 4
        mov     dword  [esp], ecx    ; 4-byte Spill
        test    edi, edi
        js      LBB4_14
LBB4_15:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     cl, byte  [ebp]
        cmp     cl, 46
        je      LBB4_19
LBB4_22:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     ebx, -1
        movsx   ecx, byte  [ebp]
        cmp     ecx, 76
        je      LBB4_30
LBB4_28:                               ;   in Loop: Header=BB4_3 Depth=1
        cmp     cl, 108
        je      LBB4_30
        mov     edx, ecx
        cmp     cl, 104
        je      LBB4_30
        mov     ecx, -1
        movsx   edx, dl
        add     edx, -37
        cmp     edx, 83
        ja      LBB4_36
LBB4_31:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     dword  [esp + 4], 10 ; 4-byte Folded Spill
        jmp     dword  [4*edx + LJTI4_1]
LBB4_32:                               ;   in Loop: Header=BB4_3 Depth=1
        or      eax, 2
LBB4_33:                               ;   in Loop: Header=BB4_3 Depth=1
        cmp     ecx, 108
        jne     LBB4_52
LBB4_34:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     ecx, dword  [esp]    ; 4-byte Reload
        mov     edx, dword  [ecx]
        add     ecx, 4
        mov     dword  [esp], ecx    ; 4-byte Spill
        jmp     LBB4_72
LBB4_16:                               ;   in Loop: Header=BB4_3 Depth=1
        xor     edi, edi
LBB4_17:                               ;   Parent Loop BB4_3 Depth=1
        lea     edx, [edi + 4*edi]
        movsx   ecx, cl
        lea     edi, [ecx + 2*edx - 48]
        movsx   ecx, byte  [ebp + 1]
        inc     ebp
        mov     edx, ecx
        add     edx, -48
        cmp     edx, 9
        jbe     LBB4_17
        cmp     cl, 46
        jne     LBB4_22
LBB4_19:                               ;   in Loop: Header=BB4_3 Depth=1
        movsx   edx, byte  [ebp + 1]
        lea     ecx, [ebp + 1]
        mov     ebx, edx
        add     ebx, -48
        cmp     ebx, 9
        jbe     LBB4_23
        cmp     dl, 42
        jne     LBB4_26
        mov     ecx, dword  [esp]    ; 4-byte Reload
        add     ebp, 2
        mov     ebx, dword  [ecx]
        add     ecx, 4
        mov     dword  [esp], ecx    ; 4-byte Spill
        mov     ecx, ebp
        test    ebx, ebx
        jns     LBB4_27
        jmp     LBB4_26
LBB4_23:                               ;   in Loop: Header=BB4_3 Depth=1
        xor     ebx, ebx
LBB4_24:                               ;   Parent Loop BB4_3 Depth=1
        lea     ebx, [ebx + 4*ebx]
        movsx   edx, dl
        lea     ebx, [edx + 2*ebx - 48]
        movsx   edx, byte  [ecx + 1]
        inc     ecx
        mov     ebp, edx
        add     ebp, -48
        cmp     ebp, 9
        jbe     LBB4_24
        mov     ebp, ecx
        test    ebx, ebx
        jns     LBB4_27
LBB4_26:                               ;   in Loop: Header=BB4_3 Depth=1
        xor     ebx, ebx
        mov     ebp, ecx
LBB4_27:                               ;   in Loop: Header=BB4_3 Depth=1
        movsx   ecx, byte  [ebp]
        cmp     ecx, 76
        jne     LBB4_28
LBB4_30:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     dl, byte  [ebp + 1]
        inc     ebp
        movsx   edx, dl
        add     edx, -37
        cmp     edx, 83
        jbe     LBB4_31
LBB4_36:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     byte  [esi], 37
        mov     al, byte  [ebp]
        test    al, al
        je      LBB4_74
        mov     byte  [esi + 1], al
        add     esi, 2
        inc     ebp
        mov     al, byte  [ebp]
        cmp     al, 37
        jne     LBB4_2
        jmp     LBB4_3
LBB4_14:                               ;   in Loop: Header=BB4_3 Depth=1
        neg     edi
        or      eax, 16
        mov     cl, byte  [ebp]
        cmp     cl, 46
        je      LBB4_19
        jmp     LBB4_22
LBB4_38:
        mov     byte  [esi], 37
        jmp     LBB4_75
LBB4_39:                               ;   in Loop: Header=BB4_3 Depth=1
        test    al, 16
        jne     LBB4_44
        dec     edi
        test    edi, edi
        jle     LBB4_44
        sub     esp, 4
        push    edi
        push    32
        push    esi
        call    memset
        add     esp, 16
LBB4_42:                               ;   Parent Loop BB4_3 Depth=1
        inc     esi
        dec     edi
        jg      LBB4_42
        xor     edi, edi
LBB4_44:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     ecx, dword  [esp]    ; 4-byte Reload
        dec     edi
        mov     al, byte  [ecx]
        add     ecx, 4
        mov     dword  [esp], ecx    ; 4-byte Spill
        mov     byte  [esi], al
        inc     esi
        test    edi, edi
        jle     LBB4_70
        sub     esp, 4
        push    edi
        push    32
        push    esi
        call    memset
        add     esp, 16
LBB4_46:                               ;   Parent Loop BB4_3 Depth=1
        inc     esi
        dec     edi
        jg      LBB4_46
        jmp     LBB4_70
LBB4_47:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     ecx, dword  [esp]    ; 4-byte Reload
        mov     edx, esi
        inc     ebp
        sub     edx, dword  [esp + 32]
        mov     eax, dword  [ecx]
        add     ecx, 4
        mov     dword  [esp], ecx    ; 4-byte Spill
        mov     dword  [eax], edx
        mov     al, byte  [ebp]
        cmp     al, 37
        jne     LBB4_2
        jmp     LBB4_3
LBB4_48:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     dword  [esp + 4], 8  ; 4-byte Folded Spill
        cmp     ecx, 108
        je      LBB4_34
        jmp     LBB4_52
LBB4_49:                               ;   in Loop: Header=BB4_3 Depth=1
        xor     ecx, ecx
        cmp     edi, -1
        mov     edx, 8
        sete    cl
        cmove   edi, edx
        or      eax, ecx
        mov     ecx, dword  [esp]    ; 4-byte Reload
        mov     edx, dword  [ecx]
        add     ecx, 4
        mov     dword  [esp], ecx    ; 4-byte Spill
        mov     ecx, esi
        push    eax
        push    ebx
        push    edi
        push    16
        jmp     LBB4_73
LBB4_50:                               ;   in Loop: Header=BB4_3 Depth=1
        or      eax, 32
LBB4_51:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     dword  [esp + 4], 16 ; 4-byte Folded Spill
        cmp     ecx, 108
        je      LBB4_34
LBB4_52:                               ;   in Loop: Header=BB4_3 Depth=1
        cmp     ecx, 104
        mov     ecx, dword  [esp]    ; 4-byte Reload
        mov     edx, dword  [ecx]
        lea     ecx, [ecx + 4]
        mov     dword  [esp], ecx    ; 4-byte Spill
        jne     LBB4_72
        test    al, 2
        jne     LBB4_71
        movzx   edx, dx
        jmp     LBB4_72
LBB4_55:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     ecx, dword  [esp]    ; 4-byte Reload
        test    ebx, ebx
        mov     edx, dword  [ecx]
        mov     ecx, edx
        mov     dword  [esp + 4], edx ; 4-byte Spill
        je      LBB4_60
        mov     edx, dword  [esp + 4] ; 4-byte Reload
        mov     cl, byte  [edx]
        test    cl, cl
        je      LBB4_60
        mov     ecx, dword  [esp + 4] ; 4-byte Reload
        dec     ebx
LBB4_58:                               ;   Parent Loop BB4_3 Depth=1
        lea     edx, [ecx + 1]
        add     ebx, -1
        jae     LBB4_60
        movzx   ecx, byte  [ecx + 1]
        test    cl, cl
        mov     ecx, edx
        jne     LBB4_58
LBB4_60:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     ebx, edx
        mov     dword  [esp + 8], edx ; 4-byte Spill
        sub     ebx, dword  [esp + 4] ; 4-byte Folded Reload
        test    al, 16
        jne     LBB4_65
        cmp     ebx, edi
        jge     LBB4_76
        mov     eax, dword  [esp + 4] ; 4-byte Reload
        lea     eax, [edi + eax]
        sub     eax, edx
        sub     esp, 4
        push    eax
        push    32
        push    esi
        call    memset
        add     esp, 16
LBB4_63:                               ;   Parent Loop BB4_3 Depth=1
        dec     edi
        inc     esi
        cmp     ebx, edi
        jl      LBB4_63
        mov     edi, dword  [esp + 4] ; 4-byte Reload
        not     edi
        add     edi, dword  [esp + 8] ; 4-byte Folded Reload
LBB4_65:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     ecx, dword  [esp + 4] ; 4-byte Reload
        test    ebx, ebx
        mov     eax, ebx
        jle     LBB4_67
LBB4_66:                               ;   Parent Loop BB4_3 Depth=1
        movzx   edx, byte  [ecx]
        inc     ecx
        mov     byte  [esi], dl
        inc     esi
        dec     eax
        jne     LBB4_66
LBB4_67:                               ;   in Loop: Header=BB4_3 Depth=1
        add     dword  [esp], 4      ; 4-byte Folded Spill
        cmp     ebx, edi
        jge     LBB4_70
        mov     eax, dword  [esp + 4] ; 4-byte Reload
        add     eax, edi
        sub     eax, dword  [esp + 8] ; 4-byte Folded Reload
        sub     esp, 4
        push    eax
        push    32
        push    esi
        call    memset
        add     esp, 16
LBB4_69:                               ;   Parent Loop BB4_3 Depth=1
        dec     edi
        inc     esi
        cmp     ebx, edi
        jl      LBB4_69
LBB4_70:                               ;   in Loop: Header=BB4_3 Depth=1
        inc     ebp
        mov     al, byte  [ebp]
        cmp     al, 37
        jne     LBB4_2
        jmp     LBB4_3
LBB4_71:                               ;   in Loop: Header=BB4_3 Depth=1
        movsx   edx, dx
LBB4_72:                               ;   in Loop: Header=BB4_3 Depth=1
        mov     ecx, esi
        push    eax
        push    ebx
        push    edi
        push    dword  [esp + 16]    ; 4-byte Folded Reload
LBB4_73:                               ;   in Loop: Header=BB4_3 Depth=1
        call    number
        add     esp, 16
        mov     esi, eax
        inc     ebp
        mov     al, byte  [ebp]
        cmp     al, 37
        jne     LBB4_2
LBB4_3:                                ; =>This Loop Header: Depth=1
        inc     ebp
        xor     eax, eax
        jmp     LBB4_5
LBB4_74:
        dec     ebp
        jmp     LBB4_75
LBB4_76:                               ;   in Loop: Header=BB4_3 Depth=1
        dec     edi
        mov     ecx, dword  [esp + 4] ; 4-byte Reload
        test    ebx, ebx
        mov     eax, ebx
        jg      LBB4_66
        jmp     LBB4_67
LBB4_77:
        mov     byte  [esi], 0
        sub     esi, dword  [esp + 32]
        mov     eax, esi
        add     esp, 12
        pop     esi
        pop     edi
        pop     ebx
        pop     ebp
        ret
LJTI4_0:
        dd   LBB4_7
        dd   LBB4_11
        dd   LBB4_11
        dd   LBB4_8
        dd   LBB4_11
        dd   LBB4_11
        dd   LBB4_11
        dd   LBB4_11
        dd   LBB4_11
        dd   LBB4_11
        dd   LBB4_11
        dd   LBB4_4
        dd   LBB4_11
        dd   LBB4_9
        dd   LBB4_11
        dd   LBB4_11
        dd   LBB4_10
LJTI4_1:
        dd   LBB4_38
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_51
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_39
        dd   LBB4_32
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_32
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_47
        dd   LBB4_48
        dd   LBB4_49
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_55
        dd   LBB4_36
        dd   LBB4_33
        dd   LBB4_36
        dd   LBB4_36
        dd   LBB4_50
number:                                 ; @number
        push    ebp
        push    ebx
        push    edi
        push    esi
        sub     esp, 92
        mov     esi, ecx
        mov     ecx, dword  [esp + 124]
        mov     eax, dword  [esp + 112]
        mov     edi, edx
        mov     edx, ecx
        lea     eax, [eax - 2]
        and     edx, -2
        test    cl, 16
        cmove   edx, ecx
        xor     ebx, ebx
        cmp     eax, 14
        ja      LBB5_42
        mov     ebp, ecx
        mov     ecx, dword  [esp + 116]
        test    dl, 2
        jne     LBB5_3
        mov     dword  [esp + 8], 0  ; 4-byte Folded Spill
        test    dl, 64
        je      LBB5_13
LBB5_9:
        mov     eax, dword  [esp + 112]
        cmp     eax, 8
        je      LBB5_12
        cmp     eax, 16
        jne     LBB5_13
        add     ecx, -2
        jmp     LBB5_13
LBB5_3:
        test    edi, edi
        js      LBB5_4
        test    dl, 4
        jne     LBB5_6
        mov     ebx, edx
        and     ebx, 8
        mov     eax, ebx
        shl     bl, 2
        shr     eax, 3
        mov     dword  [esp + 8], ebx ; 4-byte Spill
        sub     ecx, eax
        test    dl, 64
        jne     LBB5_9
        jmp     LBB5_13
LBB5_4:
        mov     al, 45
        neg     edi
        dec     ecx
        mov     dword  [esp + 8], eax ; 4-byte Spill
        test    dl, 64
        jne     LBB5_9
        jmp     LBB5_13
LBB5_12:
        dec     ecx
        jmp     LBB5_13
LBB5_6:
        mov     al, 43
        dec     ecx
        mov     dword  [esp + 8], eax ; 4-byte Spill
        test    dl, 64
        jne     LBB5_9
LBB5_13:
        mov     eax, ebp
        mov     dword  [esp + 20], ecx ; 4-byte Spill
        mov     dword  [esp + 12], edx ; 4-byte Spill
        and     al, 32
        test    edi, edi
        mov     dword  [esp + 16], eax ; 4-byte Spill
        je      LBB5_45
        xor     ebp, ebp
LBB5_15:                               ; =>This Inner Loop Header: Depth=1
        mov     ebx, dword  [esp + 112]
        mov     eax, edi
        xor     edx, edx
        div     ebx
        movzx   ecx, byte  [edx + number.digits]
        or      cl, byte  [esp + 16] ; 1-byte Folded Reload
        mov     byte  [esp + ebp + 26], cl
        inc     ebp
        cmp     edi, ebx
        mov     edi, eax
        jae     LBB5_15
        jmp     LBB5_16
LBB5_45:
        mov     byte  [esp + 26], 48
        mov     ebp, 1
LBB5_16:
        mov     edi, dword  [esp + 120]
        mov     ecx, dword  [esp + 20] ; 4-byte Reload
        mov     eax, dword  [esp + 12] ; 4-byte Reload
        cmp     ebp, edi
        cmovge  edi, ebp
        sub     ecx, edi
        test    al, 17
        je      LBB5_17
        mov     edx, dword  [esp + 8] ; 4-byte Reload
        test    dl, dl
        je      LBB5_24
LBB5_23:
        mov     byte  [esi], dl
        inc     esi
LBB5_24:
        test    al, 64
        je      LBB5_29
        mov     edx, dword  [esp + 112]
        cmp     edx, 16
        je      LBB5_28
        cmp     edx, 8
        jne     LBB5_29
        mov     byte  [esi], 48
        inc     esi
LBB5_29:
        test    al, 16
        jne     LBB5_35
LBB5_30:
        test    ecx, ecx
        jle     LBB5_31
        and     al, 1
        shl     al, 4
        or      al, 32
        sub     esp, 4
        movzx   eax, al
        push    ecx
        push    eax
        push    esi
        mov     ebx, ecx
        call    memset
        mov     eax, ebx
        add     esp, 16
LBB5_33:                               ; =>This Inner Loop Header: Depth=1
        inc     esi
        dec     eax
        jg      LBB5_33
        mov     ecx, -1
        cmp     ebp, dword  [esp + 120]
        jl      LBB5_43
        jmp     LBB5_36
LBB5_17:
        test    ecx, ecx
        jle     LBB5_18
        sub     esp, 4
        push    ecx
        push    32
        push    esi
        mov     ebx, ecx
        call    memset
        mov     eax, ebx
        add     esp, 16
LBB5_20:                               ; =>This Inner Loop Header: Depth=1
        inc     esi
        dec     eax
        jg      LBB5_20
        mov     eax, dword  [esp + 12] ; 4-byte Reload
        mov     ecx, -1
        mov     edx, dword  [esp + 8] ; 4-byte Reload
        test    dl, dl
        jne     LBB5_23
        jmp     LBB5_24
LBB5_31:
        dec     ecx
        cmp     ebp, dword  [esp + 120]
        jl      LBB5_43
        jmp     LBB5_36
LBB5_28:
        mov     edx, dword  [esp + 16] ; 4-byte Reload
        mov     byte  [esi], 48
        or      dl, 88
        mov     byte  [esi + 1], dl
        add     esi, 2
        test    al, 16
        je      LBB5_30
LBB5_35:
        cmp     ebp, dword  [esp + 120]
        jge     LBB5_36
LBB5_43:
        mov     eax, edi
        sub     eax, ebp
        sub     esp, 4
        push    eax
        push    48
        push    esi
        mov     ebx, ecx
        call    memset
        mov     ecx, ebx
        add     esp, 16
LBB5_44:                               ; =>This Inner Loop Header: Depth=1
        dec     edi
        inc     esi
        cmp     ebp, edi
        jl      LBB5_44
LBB5_36:
        mov     ebx, esi
LBB5_37:                               ; =>This Inner Loop Header: Depth=1
        movzx   eax, byte  [esp + ebp + 25]
        dec     ebp
        mov     byte  [ebx], al
        lea     ebx, [ebx + 1]
        jg      LBB5_37
        test    ecx, ecx
        jle     LBB5_42
        sub     esp, 4
        push    ecx
        push    32
        push    ebx
        mov     esi, ecx
        call    memset
        mov     edx, esi
        add     esp, 16
        xor     eax, eax
LBB5_40:                               ; =>This Inner Loop Header: Depth=1
        lea     ecx, [edx + eax - 1]
        dec     eax
        test    ecx, ecx
        jg      LBB5_40
        sub     ebx, eax
LBB5_42:
        mov     eax, ebx
        add     esp, 92
        pop     esi
        pop     edi
        pop     ebx
        pop     ebp
        ret
LBB5_18:
        dec     ecx
        mov     edx, dword  [esp + 8] ; 4-byte Reload
        test    dl, dl
        jne     LBB5_23
        jmp     LBB5_24
sprintf:                                ; @sprintf
        sub     esp, 12
        mov     eax, dword  [esp + 16]
        mov     ecx, dword  [esp + 20]
        lea     edx, [esp + 24]
        mov     dword  [esp + 8], edx
        sub     esp, 4
        push    edx
        push    ecx
        push    eax
        call    vsprintf
        add     esp, 28
        ret
printf:                                 ; @printf
        push    edi
        push    esi
        sub     esp, 1028
        mov     eax, dword  [esp + 1040]
        lea     ecx, [esp + 1044]
        mov     dword  [esp], ecx
        sub     esp, 4
        lea     edi, [esp + 8]
        push    ecx
        push    eax
        push    edi
        call    vsprintf
        add     esp, 16
        mov     esi, eax
        lea     eax, [esp + 3]
LBB7_1:                                ; =>This Inner Loop Header: Depth=1
        cmp     byte  [eax + 1], 0
        lea     eax, [eax + 1]
        jne     LBB7_1
        sub     eax, edi
        sub     esp, 4
        push    eax
        push    edi
        push    0
        call    sys_write
        add     esp, 16
        mov     eax, esi
        add     esp, 1028
        pop     esi
        pop     edi
        ret
main:                                   ; @main
        sub     esp, 16
        push    14
        push    Lstr
        push    1
        call    sys_write
        add     esp, 16
        xor     eax, eax
        add     esp, 12
        ret
number.digits:
        db  "0123456789ABCDEF"

Lstr:
        db  "Hello, world!", 10, 0