import VM

import binascii
import cProfile, pstats, io

if __name__ == "__main__":
    pr = cProfile.Profile()
    vm = VM.VM(1024)

    binary = "B8 04 00 00 00" \
             "BB 01 00 00 00" \
             "B9 29 00 00 00" \
             "BA 0E 00 00 00" \
             "CD 80" \
             "E9 02 00 00 00" \
             "89 C8" \
             "B8 01 00 00 00" \
             "BB 00 00 00 00" \
             "CD 80" \
             "48 65 6C 6C 6F 2C 20 77 6F 72 6C 64 21 0A"
    binary = bytearray.fromhex(binary)

    pr.enable()
    vm.execute_bytes(binary)

    #vm.execute_file('asm/test_jmp_int.bin')
    #vm.execute_file('asm/test_push_pop.bin')
    #vm.execute_file('asm/test_call_ret.bin')
    #vm.execute_file('asm/test_add_sub.bin')
    #vm.execute_file('asm/test_lea.bin')
    #vm.execute_file('asm/test_cmp_jcc.bin')
    #vm.execute_file('asm/test_bitwise.bin')
    #vm.execute_file('asm/test_test.bin')
    #vm.execute_file('asm/test_inc_dec.bin')

    #vm.execute_file('asm/c_pointers.bin')  # exit code 1
    #vm.execute_file('asm/c_loops.bin')  # exit code 10
    pr.disable()


    def Stats():
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
