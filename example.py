import cProfile, pstats, io
import re
import VM


def Stats(pr):
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


def parse_code(code: str):
    binary = ''
    regex = re.compile("[0-9a-f]+:\s+([^\;]+)\s*;.*", re.DOTALL)

    for line in code.strip().splitlines(keepends=False):
        if line.startswith(';'):
            continue
        match = regex.match(line)
        if not match:
            raise ValueError("Malformed code!")
        binary += match.groups()[0]

    return bytearray.fromhex(binary)


if __name__ == "__main__":
    code = """
;                           section .text
;                           _start:
0:  b8 04 00 00 00          ;mov    eax,0x4   ; SYS_WRITE
5:  bb 01 00 00 00          ;mov    ebx,0x1   ; STDOUT
a:  b9 29 00 00 00          ;mov    ecx,0x29  ; address of the message
f:  ba 0e 00 00 00          ;mov    edx,0xe   ; length of the message
14: cd 80                   ;int    0x80      ; interrupt kernel
16: e9 02 00 00 00          ;jmp    0x1d      ; _exit
1b: 89 c8                   ;mov    eax,ecx   ; this is here to mess things up if JMP doesn't work
;                           _exit:
1d: b8 01 00 00 00          ;mov    eax,0x1   ; SYS_EXIT
22: bb 00 00 00 00          ;mov    ebx,0x0   ; EXIT_SUCCESS
27: cd 80                   ;int    0x80      ; interrupt kernel
; section .data
29: 48 65 6C 6C 6F 2C 20 77 6F 72 6C 64 21 0A ; "Hello, world!",10
             """

    vm = VM.VM(64)
    binary = parse_code(code)

    # pr = cProfile.Profile()
    # pr.enable()
    vm.execute_bytes(binary)
    # pr.disable()

    # Stats(pr)
