
import io
from os import PathLike
from pathlib import Path
from typing import Union, AnyStr, MutableMapping, Any

import toml

from .config_data_types import ConfigDataTypes
from .config_exceptions import DictLoadError
from ..utility.typing import Buffer, mmap


def _load_dict_from_toml_stream_or_file(
    file_path: Union[PathLike[str], Buffer[AnyStr]],
    data_type: ConfigDataTypes = ConfigDataTypes.infer,
    encoding: str = "utf-8",
) -> Union[MutableMapping[str, Any], None]:
    """Load the content of a structured text file or stream into a dictionary using one
    of the TOML parsing library (from https://github.com/uiri/toml)
    Internal function which assumes checking of file existance, accessibility and size has been done elsewhere.
    Args:
        file_path: path to the file to be parsed or opened stream or buffer
        data_type: optional, pre-defines the data type to be parsed; if not provided, data type is determined by file name's suffix or file/stream content.
        encoding: encoding type used to decode binary files/streams/buffers; ignored, if string, `Path` or file opened in text-mode is given as `file_path`
    Raises:
        DictLoadError: if the given file/stream/buffer could not be read into a dictionary (eg due to wrong syntax) and given data type is `ConfigDataTypes.toml` (otherwise, no Exception is raised, instead None is returned)
    Returns:
        dictionary with parsed file/buffer/stream content or None in case of error and no exception was raised. In case of error, resets file-pointer to 0, if open file was given.
    """

    try:
        if (hasattr(file_path, "mode") and "b" in file_path.mode) or isinstance(   # type: ignore
            file_path, (io.RawIOBase, io.BufferedIOBase, mmap)
        ):  
            return toml.loads(file_path.read().decode(encoding))  # type: ignore
        elif isinstance(file_path, io.StringIO):
            return toml.loads(file_path.getvalue())  # type: ignore
        else:
            return toml.load(file_path)  # type: ignore
    except TypeError as e:
        raise DictLoadError(
            message=f"Invalid file provided {str(file_path)}.",
            document="",
            position=0,
            line_number=0,
            column_number=0,
        )
    except toml.TomlDecodeError as e:
        if data_type == ConfigDataTypes.toml:
            raise DictLoadError(
                message=e.msg,  # type: ignore
                document=e.doc,  # type: ignore
                position=e.pos,  # type: ignore
                line_number=e.lineno,  # type: ignore
                column_number=e.colno,  # type: ignore
            )
    # on error, reset file pointer, if opened file-like was given
    if not isinstance(file_path, Path):
        file_path.seek(0)  # type: ignore

    return None
