import VM

import binascii
import cProfile, pstats, io

if __name__ == "__main__":
    pr = cProfile.Profile()
    vm = VM.VM(1024)

    binary = "B8 04 00 00 00" \
             "BB 01 00 00 00" \
             "B9 29 00 00 00" \
             "BA 0D 00 00 00" \
             "CD 80" \
             "E9 02 00 00 00" \
             "89 C8" \
             "B8 01 00 00 00" \
             "BB 00 00 00 00" \
             "CD 80" \
             "48 65 6C 6C 6F 2C 20 77 6F 72 6C 64 21 ".replace(' ', '')
    binary = binascii.unhexlify(binary)

    pr.enable()
    vm.mem.set(0, binary)
    vm.run()
    #vm.execute_file('test_stack_jmp_int')
    #vm.execute_file('test_call_ret')
    pr.disable()


    def Stats():
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
