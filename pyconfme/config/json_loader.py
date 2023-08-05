
from os import PathLike
from pathlib import Path
from typing import Union, AnyStr, MutableMapping, Any

import json

from .config_data_types import ConfigDataTypes
from .config_exceptions import DictLoadError
from ..utility.type_helpers import Buffer



def _load_dict_from_json_stream_or_file(
    file_path: Union[PathLike[str], Buffer[AnyStr]],
    data_type: ConfigDataTypes = ConfigDataTypes.infer,
    encoding: str = "utf-8",
) -> Union[MutableMapping[str, Any], None]:
    """Load the content of a structured text file or stream into a dictionary using one
    of the JSON parsing library (from standard lib https://docs.python.org/3/library/json.html)
    Internal function which assumes checking of file existance, accessibility and size has been done elsewhere.
    Args:
        file_path: path to the file to be parsed or opened stream or buffer
        data_type: optional, pre-defines the data type to be parsed; if not provided, data type is determined by file name's suffix or file/stream content.
        encoding: encoding type passed to open-function, in case path is given; ignored in case an already opened file/stream/buffer is given as `file_path`
    Raises:
        DictLoadError: if the given file/stream/buffer could not be read into a dictionary (eg due to wrong syntax) and given data type is `ConfigDataTypes.json` (otherwise, no Exception is raised, instead None is returned)
    Returns:
        dictionary with parsed file/buffer/stream content or None in case of error and no exception was raised. In case of error, resets file-pointer to 0, if open file was given.
    """

    try:
        if isinstance(file_path, Path):
            return json.loads(file_path.read_text(encoding=encoding))
        else:
            return json.load(file_path)  # type: ignore
    except AttributeError as e:
        raise DictLoadError(
            message=f"Invalid file provided {str(file_path)}.",
            document="",
            position=0,
            line_number=0,
            column_number=0,
        )
    except json.JSONDecodeError as e:
        if data_type == ConfigDataTypes.json:
            raise DictLoadError(
                message=e.msg,
                document=e.doc,
                position=e.pos,
                line_number=e.lineno,
                column_number=e.colno,
            )
    # on error, reset file pointer, if opened file-like was given
    if not isinstance(file_path, Path):
        file_path.seek(0)  # type: ignore

    return None
