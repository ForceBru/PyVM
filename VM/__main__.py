import argparse
import shlex
import logging
import sys

from . import VMKernel, ExecutionStrategy


parser = argparse.ArgumentParser()
parser.add_argument('command', help='The command to be executed')
parser.add_argument(
    '-t', '--type',
    default=ExecutionStrategy.ELF, type=lambda s: ExecutionStrategy[s.upper()],
    help='Executable type (elf, flat)'
)
parser.add_argument('-m', '--memory', default=10_000, type=int, help='The amount of memory to give to the VM (bytes)')
parser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output')
parser.add_argument('-v', '--verbose', action='store_true', default=False)
args = parser.parse_args()


if args.verbose:
    print(f'Initializing VM with {args.memory:,d} bytes of memory...')

if args.debug:
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(message)s'
    )

vm = VMKernel(args.memory)

cmd, *cmd_args = shlex.split(args.command)

if args.type == ExecutionStrategy.ELF:
    if args.verbose:
        print(f'Running ELF executable {cmd!r} with arguments {cmd_args}...')
    vm.execute(args.type, cmd, cmd_args)
elif args.type == ExecutionStrategy.FLAT:
    if cmd_args:
        raise ValueError(f'Running flat binaries with arguments is not supported yet! Arguments: {cmd_args}')
    if args.verbose:
        print(f'Running flat executable {cmd!r}...')
    vm.execute(args.type, cmd)
else:
    raise ValueError(f'Invalid executable type: {args.type}')

if args.verbose:
    print(f'Command {args.command!r} executed!')
