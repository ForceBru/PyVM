__all__ = 'dword', 'word', 'byte', 'udword', 'uword', 'ubyte'

import ctypes

# __ctype_le__ means 'LittleEndian'. Looks like a dirty hack.
# Found here: https://mail.python.org/pipermail/python-list/2015-June/692849.html
uqword = ctypes.c_uint64.__ctype_le__
udword = ctypes.c_uint32.__ctype_le__
uword  = ctypes.c_uint16.__ctype_le__
ubyte  = ctypes.c_uint8.__ctype_le__

qword = ctypes.c_int64.__ctype_le__
dword = ctypes.c_int32.__ctype_le__
word  = ctypes.c_int16.__ctype_le__
byte  = ctypes.c_int8.__ctype_le__

flt = ctypes.c_float.__ctype_le__
dbl = ctypes.c_double.__ctype_le__
