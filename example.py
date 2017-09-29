import cProfile, pstats, io
import VM


def Stats(pr):
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


if __name__ == "__main__":
    # pr = cProfile.Profile()
    vm = VM.VM(128)

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

    # pr.enable()
    vm.execute_bytes(binary)
    # pr.disable()

    # Stats(pr)