__all__ = 'dword', 'word', 'byte', 'udword', 'uword', 'ubyte'

import ctypes

# __ctype_le__ means 'LittleEndian'. Looks like a dirty hack, found here: https://mail.python.org/pipermail/python-list/2015-June/692849.html
udword = ctypes.c_uint32.__ctype_le__
uword  = ctypes.c_uint16.__ctype_le__
ubyte  = ctypes.c_uint8.__ctype_le__

dword = ctypes.c_int32.__ctype_le__
word  = ctypes.c_int16.__ctype_le__
byte  = ctypes.c_int8.__ctype_le__