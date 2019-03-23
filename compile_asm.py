import subprocess
from pathlib import Path


def find_nasm_executable(root=".") -> Path:
    '''
    :param root: Path to search in.
    :return: Path to the latest `nasm` executable available
    '''

    root = Path(root)

    if not root.is_absolute():
        root = Path.cwd() / root

    if not root.is_dir():
        raise ValueError(f'The root path {root!r} is not a directory!')

    nasm_paths = [path for path in root.glob("nasm-*") if path.is_dir()]

    nasm_paths.sort(key=lambda path: path.name)
    nasm_executable = nasm_paths[-1] / 'nasm'

    if not nasm_executable.is_file():
        raise ValueError(f'File {nasm_executable!r} is a directory.')

    return nasm_executable


def compile_one(nasm_executable: Path, asm_file: Path, include_path=None):
    if include_path is None:
        include_path = asm_file.parent

    if not include_path.is_dir():
        raise ValueError(f'The include path {include_path!r} is not a directory!')

    if not asm_file.is_file():
        raise ValueError(f'The assembly file {asm_file!r} is not a file!')

    output_path = asm_file.parent / "bin" / (asm_file.name.rsplit(".")[0] + ".bin")

    args = str(nasm_executable), "-f", "bin", "-I", str(include_path), "-o", str(output_path), str(asm_file)

    return subprocess.run(args, capture_output=True, timeout=5)


def compile_many(nasm_executable: Path,
                 files_path: Path,
                 exclude_files=(),
                 include_path=None,
                 clean=False):
    out_path = files_path / "bin"

    if clean:
        for bin_file in out_path.glob("*.bin"):
            bin_file.unlink()

    failed = {}

    for asm_file in files_path.glob("*.s"):
        if asm_file.name in exclude_files or asm_file in exclude_files:
            print(f"Skipping: {asm_file}")
            continue

        print(f"Compiling: {asm_file}")
        ret = compile_one(nasm_executable, asm_file, include_path)

        if ret.returncode != 0:
            failed[asm_file] = ret
            print(f"[ERROR] Failed to build: {asm_file} - {ret}")

        if ret.stdout:
            print(f"[BEGIN STDOUT]")
            print(ret.stdout.decode())
            print(f"[END STDOUT]")

    return failed


def compile_all():
    executable = find_nasm_executable()
    filepath = Path.cwd() / "asm"

    failed = compile_many(executable, filepath, exclude_files=['startup.s'])

    for fname, result in failed.items():
        print(f"Error message for {fname}:")
        print(result.stderr.decode())
    else:
        print("Built successfully!")


if __name__ == '__main__':
    compile_all()

    import VM

    vm = VM.VM(1024)
    vm.execute_file('asm/bin/c_float.bin')
