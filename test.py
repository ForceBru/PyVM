import VM

import binascii
import cProfile, pstats, io

if __name__ == "__main__":
    pr = cProfile.Profile()
    vm = VM.VM(1024)

    binary = "B8 00 04 00 00 B9 00 08 00 00 01 C1 B8 01 00 00 00 BB 00 00 00 00 CD 80".replace(' ', '')
    binary = binascii.unhexlify(binary)

    pr.enable()
    vm.mem.set(0, binary)
    vm.run()
    #vm.execute_file('test_stack_jmp_int')
    #vm.execute_file('test_call_ret')
    pr.disable()

    print(VM.to_int(vm.reg.get(1, 4)))


    def Stats():
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
