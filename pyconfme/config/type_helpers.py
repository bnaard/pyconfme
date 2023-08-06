from typing import Union, IO, AnyStr
from io import BufferedIOBase, RawIOBase, TextIOBase, TextIOWrapper
from mmap import mmap
from os import PathLike

# typings analoguous to pandas' read_* functions, which allow to read from any url-like string or opened stream object
Buffer = Union[IO[AnyStr], RawIOBase, BufferedIOBase, TextIOBase, TextIOWrapper, mmap]
FileOrBuffer = Union[str, Buffer[AnyStr]]
FilePathOrBuffer = Union[PathLike[str], FileOrBuffer[AnyStr]]

