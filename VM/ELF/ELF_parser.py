import struct

__all__ = ('ELF_parser', )

class ELF_meta(type):
    def __new__(cls, name, bases, dict):
        if '__annotations__' not in dict:
            return super().__new__(cls, name, bases, dict)
            
        layouts = {}
        current_entries = []
        current_layout = ''
        for entry, annot in dict['__annotations__'].items():
            if isinstance(annot, cls):
                if current_layout:
                    layouts[tuple(current_entries)] = current_layout
                    current_entries, current_layout = [], ''
                layouts[('_' + entry, )] = annot
            elif isinstance(annot, str):
                current_entries.append('_' + entry)
                current_layout += annot
            else:
                raise ValueError(f'Unexpected type in annotation for {name}.{entry}: {annot!r} of type {type(annot)}')
            
            try:
                converter = dict[entry]  # must be a function of one argument
                if not hasattr(converter, '__call__'):
                    raise ValueError(f'Converter for entry {name}.{entry} must be callable (got {converter!r})')
            except KeyError:
                converter = lambda x: x
                
            dict[entry] = property(lambda self, e=entry, c=converter: c(self.__getattribute__('_' + e)))
            dict['_' + entry] = 0
        
        if current_layout:
            layouts[tuple(current_entries)] = current_layout
        
        dict['_layouts'] = {
            key: (
                struct.Struct(value)
                if isinstance(value, str) else value
                )
            for key, value in layouts.items()
            }
        dict['size'] = sum(
            val.size
            for val in dict['_layouts'].values()
            )
        dict['_name'] = name
        
        def __init__(self, stream):
            self.__RAW = b''
            for entries, parser in self._layouts.items():
                if isinstance(parser, struct.Struct):
                    _raw = stream.read(parser.size)
                    parsed = parser.unpack(_raw)
                    self.__RAW += _raw
                else:
                    parsed = parser(stream),
                    self.__RAW += parsed[0].__RAW
                    
                for name, value in zip(entries, parsed):
                    assert name.startswith('_')
                    setattr(self, name, value)
                
            self.__repr = None
            self.__len = len(self.__RAW)
                
        def __repr__(self):
            if self.__repr is None:
                ret = self._name + ' {\n'
                for entries, parser in self._layouts.items():
                    if isinstance(parser, struct.Struct):
                        for name in entries:
                            data = self.__getattribute__(name[1:])
                            if isinstance(data, bytes):
                                data = '0x' + data.hex()
                            ret += f'\t{name[1:]} = {data},\n'
                    else:
                        for name in entries:
                            data = self.__getattribute__(name)
                            lines = repr(data).splitlines()
                            data = lines[0] + '\n' + '\n'.join('\t' + s for s in lines[1:])
                            ret += f'\t{name[1:]} = {data},\n'
                self.__repr = ret + '}'
            return self.__repr
            
        def __bytes__(self):
            return self.__RAW
            
        def __eq__(self, other):
            return self.__RAW == other.__RAW
            
        def __hash__(self):
            return hash(self.__RAW)
            
        def __len__(self):
            return self.__len
                
        dict['__init__'] = __init__
        dict['__repr__'] = __repr__
        dict['__bytes__'] = __bytes__
        dict['__eq__'] = __eq__
        dict['__hash__'] = __hash__
        dict['__len__'] = __len__
            
        return super().__new__(cls, name, bases, dict)


class ELF_parser(metaclass=ELF_meta):
    ...

