"""This module implements methods to load dictonaries from text-based configuration files."""

import os
import errno
from pathlib import Path
from typing import Union, AnyStr, MutableMapping, Any

from .config_data_types import ConfigDataTypes
from .config_exceptions import DictLoadError
from .json_loader import _load_dict_from_json_stream_or_file
from .toml_loader import _load_dict_from_toml_stream_or_file    # pyright: ignore[reportMissingImports]
from .yaml_loader import _load_dict_from_yaml_stream_or_file    # pyright: ignore[reportMissingImports]
from ..utility.typing import FilePathOrBuffer


MAX_CONFIG_FILE_SIZE = 1024 * 1024 * 1024




def _determine_config_file_type(file_path: Union[Path, str]) -> ConfigDataTypes:
    """Determine the file type of a given file from its suffix and return determined type as enum-value
    Currently the following data-types are known:

    Suffixes | Return Value | Data Type
    ------ | ---- | ----
    `.json`, `.jsn` | `ConfigDataTypes.json` | JSON
    `.toml`, `.tml`, `.ini`, `.config`, `.cfg` | `ConfigDataTypes.toml` | TOML/INI
    `.yaml`, `.yml` | `ConfigDataTypes.yaml` | YAML
    anything else | `ConfigDataTypes.unknown` | unknown

    Args:
        file_path: path to the file for which the type shall be determined
    Returns:
        enum-value determining the data type or a enum-value for an unknown data type
    Example:
    ```python
    >>> from pyconfme.config.config_loader import _determine_config_file_type
    >>> _determine_config_file_type("my_config.ini")
    <ConfigDataTypes.toml: 'toml'>

    ```
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    if file_path.suffix.lower() in [".json", ".jsn"]:
        return ConfigDataTypes.json
    elif file_path.suffix.lower() in [
        ".toml",
        ".tml",
        ".ini",
        ".config",
        ".cfg",
    ]:
        return ConfigDataTypes.toml
    elif file_path.suffix.lower() in [".yml", ".yaml"]:
        return ConfigDataTypes.yaml
    else:
        return ConfigDataTypes.unknown






def load_dict_from_file(
    file_path: FilePathOrBuffer,
    data_type: ConfigDataTypes = ConfigDataTypes.infer,
    encoding: str = "utf-8",
    max_file_size: int = MAX_CONFIG_FILE_SIZE,
) -> MutableMapping[str, Any]:
    """Load the content of a structured text file or stream into a dictionary using one
    of the standard parsing libraries (eg. PyYaml).

    Depending on the determined file type, the files are parsed using the following parsers:

    Data Type | Parser
    ---- | -----------
    `ConfigDataTypes.json` | Python standard-lib [JSON parser](https://docs.python.org/3/library/json.html#json.JSONDecodeError)
    `ConfigDataTypes.toml` | [toml parser](https://pypi.org/project/toml/)
    `ConfigDataTypes.yaml` | [PyYAML parser](https://pyyaml.org/)
    `ConfigDataTypes.infer`| try to determine one of the above by checking file suffix or by parsing the buffer/stream without errors
    `ConfigDataTypes.unknown`| raises `ValueError()`

    If `data_type` is `ConfigDataTypes.infer` (the standard), then the function tries to determine the file/stream/buffer
    content in the following order:
    1. if it is a file, check file suffix against known data-types, see: [_determine_config_file_type][pyconfme.config.config_file_loaders._determine_config_file_type]
    2. if it is not a file or suffix is not known, try to load the data into a dictionary, trying one parser after the other
    3. if a data format has been provided in `data_type`, but parsing did not succeed, raise a DictLoadError exception

    When trying parsers, JSON is always preferred, then TOML, finally YAML. This order is adapted, if
    a `data_type` has been provided.

    Data Type | Load order
    ---- | -----------
    `ConfigDataTypes.json` | JSON, TOML, YAML
    `ConfigDataTypes.toml` | TOML, JSON, YAML
    `ConfigDataTypes.yaml` | YAML, JSON, TOML
    `ConfigDataTypes.unknown`| JSON, TOML, YAML

    Args:
        file_path: path to the file to be parsed or opened stream or buffer
        data_type: optional, pre-defines the data type to be parsed; if `ConfigDataTypes.unknown` or `ConfigDataTypes.infer`, data type is tried to be determined by file name's suffix or file/stream content.
        encoding: encoding type passed to an open-function, in case path is given; ignored in case an already opened file/stream/buffer is given as `file_path`
        max_file_size: maximum size a config file may have, otherwise an exception is raised
    Raises:
        DictLoadError: if the given file/stream/buffer could not be read into a dictionary (eg due to wrong syntax)
        ValueError: if trying to read a file whose size > max_file_size
        FileNotFoundError: if `file_path` could not be resolved and/or file was not accessible
        IsADirectoryError: if `file_path` could be resolved, but is a directory instead of a file
    Returns:
        dictionary with parsed file/buffer/stream content
    Example:
    ```python
    >>> from tempfile import mkdtemp
    >>> from shutil import rmtree
    >>> from pydantic import BaseSettings
    >>> from pyconfme.config.config_loader import load_dict_from_file
    >>> # create a temporary config file for this example
    >>> dirpath = mkdtemp()
    >>> temp_config_name = Path(dirpath) / "config.ini"
    >>> temp_config = open(temp_config_name, "wt")
    >>> _ = temp_config.write('foobar = "johndoe"')
    >>> temp_config.close()
    >>> temp_config = open(temp_config_name)
    >>> # load dictionary from file, file type is determined by trying to parse content w/o error
    >>> load_dict_from_file(temp_config)
    {'foobar': 'johndoe'}
    >>> temp_config.close()
    >>> rmtree(dirpath)

    ```
    """
    if file_path is None:
        raise ValueError("Data input object is None.")
    if isinstance(file_path, str):
        file_path = Path(file_path)

    determined_data_type = data_type

    # if the given input is a path to a file try to make sure it exists
    # and is readable. Also try to determine the data type by looking at
    # the file suffix, in case the function's caller has not defined the data type
    if isinstance(file_path, Path):
        file_path = file_path.resolve()

        if not file_path.is_file():
            if not file_path.exists():
                raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), str(file_path)
                )
            if file_path.is_dir():
                raise IsADirectoryError(
                    errno.ENOENT, "Is a directory instead of a file", str(file_path)
                )

        file_size = file_path.stat().st_size
        if file_size > max_file_size:
            raise ValueError(
                f"File {str(file_path)}: File size {file_size} exceeds max allowed size"
                f" {max_file_size}."
            )

        determined_data_type = (
            _determine_config_file_type(file_path)
            if data_type == ConfigDataTypes.infer
            else data_type
        )

    # set the order in which file is tried to be loaded in a way that a given (by argument
    # or by file-ending) data-type is done first, then json as this is the most significant
    # regarding the data and finally the remaining types.
    resolve_order = [ConfigDataTypes.json, ConfigDataTypes.toml, ConfigDataTypes.yaml]
    if determined_data_type == ConfigDataTypes.toml:
        resolve_order = [
            ConfigDataTypes.toml,
            ConfigDataTypes.json,
            ConfigDataTypes.yaml,
        ]
    elif determined_data_type == ConfigDataTypes.yaml:
        resolve_order = [
            ConfigDataTypes.yaml,
            ConfigDataTypes.json,
            ConfigDataTypes.toml,
        ]

    for resolve_data_type in resolve_order:
        if resolve_data_type == ConfigDataTypes.json:
            result = _load_dict_from_json_stream_or_file(
                file_path, determined_data_type, encoding=encoding
            )
            if result is not None:
                return result

        elif resolve_data_type == ConfigDataTypes.toml:
            result = _load_dict_from_toml_stream_or_file(
                file_path, determined_data_type, encoding=encoding
            )
            if result is not None:
                return result

        elif resolve_data_type == ConfigDataTypes.yaml:
            result = _load_dict_from_yaml_stream_or_file(
                file_path, determined_data_type, encoding=encoding
            )
            if result is not None:
                return result

    raise DictLoadError(
        message=(
            f"Format of config data {str(file_path)} (type {type(file_path)}) could not"
            " be determined to be one of"
            f" [{', '.join(ConfigDataTypes.allowed_names())}]."
        ),
        document=file_path.read_text() if isinstance(file_path, Path) else file_path.read(),  # type: ignore
        position=0,
        line_number=0,
        column_number=0,
    )
