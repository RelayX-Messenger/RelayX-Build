"""                   Chunker.py
This is the raw chunker module that chunks and returns the chunk index and file content (images, not txt) in bytes.

"""
import ctypes, os
from ctypes import c_int, c_size_t, c_char_p, POINTER, Structure
from RelayX.utils.config import libs_dir

class Chunk(Structure):
    _fields_ = [("index", c_int),
                ("data", ctypes.POINTER(ctypes.c_char)),
                ("len", c_size_t)]
    
lib = ctypes.CDLL(os.path.join(libs_dir,"chunker.so"))

lib.chunk_file.restype = POINTER(Chunk)
lib.chunk_file.argtypes = [c_char_p, c_size_t, POINTER(c_int)]
lib.free_chunks.argtypes = [POINTER(Chunk), c_int]

def chunk_file(path, chunk_size=1048576):
    count = c_int()
    chunks_ptr = lib.chunk_file(path.encode(), chunk_size, ctypes.byref(count))
    if not chunks_ptr:
        return None
    
    result = {}
    for i in range(count.value):
        chunk = chunks_ptr[i]
        result[chunk.index] = bytes(chunk.data[:chunk.len])
    
    lib.free_chunks(chunks_ptr, count.value)
    return result