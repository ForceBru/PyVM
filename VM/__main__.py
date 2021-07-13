# Import modules
import argparse, shlex, logging, sys
from . import VMKernel, ExecutionStrategy

# Get args 
parser = argparse.ArgumentParser()
parser.add_argument('command', help='The command to be executed')
# `-t` or `--type` arg. 
parser.add_argument(
    '-t', '--type',
    default=ExecutionStrategy.ELF, type=lambda s: ExecutionStrategy[s.upper()],
    help='Executable type (elf, flat)'
)
parser.add_argument('-m', '--memory', default=10_000, type=int, help='The amount of memory to give to the VM (bytes)')   # Memory arg
parser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output')                     # Debug arg
parser.add_argument('-v', '--verbose', action='store_true', default=False)                                               # Verbose arg
args = parser.parse_args() # Finish args


if args.verbose:
    print(f'Initializing VM with {args.memory:,d} bytes of memory...') # Print memory info

# Check if debugging arg was called, if so set the logging level to debug.
if args.debug:
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(message)s'
    )

# Setup VM w/ mem
vm = VMKernel(args.memory)

cmd, *cmd_args = shlex.split(args.command) # Command define

if args.type == ExecutionStrategy.ELF:
    if args.verbose:
        print(f'Running ELF executable {cmd!r} with arguments {cmd_args}...') # Print ELF msg if verbose arg was called. 
    vm.execute(args.type, cmd, cmd_args)
elif args.type == ExecutionStrategy.FLAT:
    if cmd_args:
        raise ValueError(f'Running flat binaries with arguments is not supported yet! Arguments: {cmd_args}') # Raise an error to the user if the user called an unsupported command.
    if args.verbose:
        print(f'Running flat executable {cmd!r}...') # Print running if verbose arg was called. 
    vm.execute(args.type, cmd)
else:
    raise ValueError(f'Invalid executable type: {args.type}') # Raise an error if the user called an "invalid" executable. 

if args.verbose:
    print(f'Command {args.command!r} executed!') # Print completed command if verbose arg was called.
