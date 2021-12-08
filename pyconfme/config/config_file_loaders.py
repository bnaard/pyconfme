"""This module implements methods to load dictonaries from text-based configuration files.
"""  # noqa: E501

import sys
import os
import io
from os import PathLike
import errno
from pathlib import Path
import yaml
import toml
import json
from functools import partial
from typing import Any, MutableMapping, Dict, Callable, cast, Union, Sequence, AnyStr
from pydantic import BaseSettings
from .config_data_types import ConfigDataTypes
from ..utility.typing import FilePathOrBuffer, Buffer, mmap
from ..utility.dict_deep_update import dict_deep_update

MAX_CONFIG_FILE_SIZE = 1024 * 1024 * 1024


class DictLoadError(Exception):
    """Exception for any file-loading or parsing error when parsing files for dictionaries with different
    libraries (eg. PyYaml).
    """

    def __init__(
        self,
        message: str,
        position: int = None,
        document: str = None,
        line_number: int = None,
        column_number: int = None,
    ):
        """Create new DictLoadException
        Args:
            message: an error message from the parsing library describing the nature of the parsing error.
            document: full or parts of the documents parsed into a dict (actual content depends on parsing library)
            position: character position where the parsing error occurred, counting from document start
            line_number: line number in the read file where the parsing error occurred
            column_number: column number in the line where the parsing error occurred
        """

        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.message = message
        self.document = document
        self.position = position
        self.line_number = line_number
        self.column_number = column_number


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
    >>> from pyconfme.config.config_file_loaders import _determine_config_file_type
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


def _load_dict_from_yaml_stream_or_file(
    file_path: Union[PathLike[str], Buffer[AnyStr]],
    data_type: ConfigDataTypes = ConfigDataTypes.infer,
    encoding: str = "utf-8",
) -> Union[MutableMapping[str, Any], None]:
    """Load the content of a structured text file or stream into a dictionary using one
    of the YAML parsing library (from https://pyyaml.org/)
    Internal function which assumes checking of file existance, accessibility and size has been done elsewhere.
    Args:
        file_path: path to the file to be parsed or opened stream or buffer
        data_type: optional, pre-defines the data type to be parsed; if not provided, data type is determined by file name's suffix or file/stream content.
        encoding: encoding type passed to open-function, in case path is given; ignored in case an already opened file/stream/buffer is given as `file_path`
    Raises:
        DictLoadError: if the given file/stream/buffer could not be read into a dictionary (eg due to wrong syntax) and given data type is `ConfigDataTypes.yaml` (otherwise, no Exception is raised, instead None is returned)
    Returns:
        dictionary with parsed file/buffer/stream content or None in case of error and no exception was raised. In case of error, resets file-pointer to 0, if open file was given.
    """

    try:
        if isinstance(file_path, Path):
            return yaml.safe_load(file_path.read_text(encoding=encoding))
        else:
            return yaml.safe_load(file_path)  # type: ignore
    except AttributeError as e:
        raise DictLoadError(
            message=f"Invalid file provided {str(file_path)}.",
            document="",
            position=0,
            line_number=0,
            column_number=0,
        )
    except yaml.YAMLError as e:
        if data_type == ConfigDataTypes.yaml:
            if hasattr(e, 'problem_mark'):
                raise DictLoadError(
                    message=f"YAML syntax error. {e.problem_mark}", # type: ignore
                )
            else:
                raise DictLoadError(
                    message=(
                        f" {str(file_path)}."
                        "Undetermined error while trying to parse as yaml file"
                    )
                )

    # on error, reset file pointer, if opened file-like was given
    if not isinstance(file_path, Path):
        file_path.seek(0)  # type: ignore

    return None


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
    a `data_type`has been provided.

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
    >>> from pyconfme.config.config_file_loaders import load_dict_from_file
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


def _settings_config_load(
    settings: BaseSettings,
    file_path: Union[FilePathOrBuffer, Sequence[FilePathOrBuffer]] = None,
    data_type: ConfigDataTypes = ConfigDataTypes.infer,
    encoding: str = "utf-8",
    error_handling: str = "propagate",
) -> Dict[str, Any]:
    """Loads settings from a file, stream or buffer into a dictionary that can be loaded by pydantic into settings classes.
    This function is not intended to be called directly, but to be used in connection [get_settings_config_load_function][pyconfme.config.config_file_loaders.get_settings_config_load_function]
    In case of permission errors or load errors the standard behaviour of
    this function is to propagate the exceptions to the caller. If successful, this
    function loads the first data source found/accessible/readable into a dictionary
    and returns this dictionary so that pydantic can try to set values in settings from it. All further
    sources (e.g. not found files) do not lead to exceptions or abortion, but are silently discarded.

    Args:
        file_path: path, list of paths, stream or list of streams to configuration data
        data_type: type of configuration data, if known or pre-defined
        encoding: encoding type passed to an open-function, in case path is given; ignored in case an already opened file/stream/buffer is given as `file_path`
        error_handling: one of `["abort", "ignore", "propagate"]`, where
            `abort` calls `sys-exit()` on load error,
            `ignore` does nothing and ultimatley returns an empty dictionary, if no data could be loaded and
            `propagate` raises the exceptions and leaves handling to the caller
            Default to `propagate`, if no value or `None` is given.
    Raises:
        ValueError: if error_handling is not one of `["abort", "ignore", "propagate"]` or if file_path is None
        IOError: if eg. permission to a given file is denied and error_handling is `propagate`
        DictLoadError: if the given data could not be read into a dictionary (eg due to wrong syntax)
    Returns:
        a dictionary with the values and structures read from the given file, stream or buffer

    """
    allowed_error_handling = ["abort", "ignore", "propagate"]
    if error_handling is None:
        error_handling = "propagate"
    if error_handling not in allowed_error_handling:
        raise ValueError(
            f"Invalid error handling type. Expected one of: {allowed_error_handling}"
        )

    if file_path is None:
        if error_handling == "abort":
            print(f"File path is not a valid type.\nAbort!")
            sys.exit()
        elif error_handling == "propagate":
            raise ValueError("File path is not a valid type.")
        else:
            return {}
    config_data_elements: Sequence[FilePathOrBuffer] = list()
    if isinstance(file_path, list):
        config_data_elements = file_path
    elif isinstance(file_path, tuple):
        config_data_elements = list(file_path)
    else:
        config_data_elements = [file_path]  # type: ignore

    result_dict: Dict[str, Any] = {}

    for config_data in config_data_elements:
        exists = False
        if isinstance(config_data, str):
            config_data = Path(config_data)
        if isinstance(config_data, Path):
            config_data = config_data.resolve()
            exists = config_data.is_file()
        else:
            exists = True

        if exists:
            try:
                load_result: Dict[str, Any] = cast(
                    Dict[str, Any],
                    load_dict_from_file(config_data, data_type, encoding=encoding),
                )
                dict_deep_update(result_dict, load_result) # type: ignore

            except DictLoadError as e:
                if error_handling == "abort":
                    print(
                        f"{e.message}\nContext:\n{e.document}\nPosition ="
                        f" {e.position}, line number = {e.line_number},"
                        f" column_number = {e.column_number}"
                    )
                    sys.exit()
                elif error_handling == "propagate":
                    raise e

            except IOError as e:
                # catch permission errors, which are propagated instead of returning false for is_file()
                if error_handling == "abort":
                    print(f"{e}\nAbort!")
                    sys.exit()
                elif error_handling == "propagate":
                    raise e

    return result_dict


def get_settings_config_load_function(
    file_path: Union[FilePathOrBuffer, Sequence[FilePathOrBuffer]] = None,
    data_type: ConfigDataTypes = ConfigDataTypes.infer,
    encoding: str = "utf-8",
    error_handling: str = "abort",
) -> Callable[[BaseSettings], Dict[str, Any]]:
    """
    Returns a function that can be used in a Config class in pydantic's
    BaseSettings classes to load configurations from predefined file location(s).
    Args:
        file_path: path or list of paths to configuration files, streams or buffers
        data_type: type of configuration data, if known/pre-defined
        encoding: encoding type passed to an open-function, in case path is given; ignored in case an already opened file/stream/buffer is given as `file_path`
        error_handling: one of `["abort", "ignore", "propagate"]`, where
            `abort` calls `sys-exit()` on load error,
            `ignore` does nothing and ultimatley returns an empty dictionary, if no data could be loaded and
            `propagate` raises the exceptions and leaves handling to the caller
    Raises:
        ValueError: if error_handling is not one of `["abort", "ignore", "propagate"]`
    Returns:
        a function that returns a dictionary with values read from file, buffer or stream or empty dict,
        in case of any ignored error. See [pydantic documentation](https://pydantic-docs.helpmanual.io/usage/settings/)

    Example:
    Adapted from [pydantic documentation](https://pydantic-docs.helpmanual.io/usage/settings/#adding-sources).
    ```python
    >>> from tempfile import mkdtemp
    >>> from shutil import rmtree
    >>> from pydantic import BaseSettings
    >>> from pyconfme import get_settings_config_load_function
    >>> # create a temporary config file for this example
    >>> dirpath = mkdtemp()
    >>> temp_config_name = Path(dirpath) / "config.ini"
    >>> temp_config = open(temp_config_name, "wt")
    >>> _ = temp_config.write('foobar = "johndoe"')
    >>> temp_config.close()
    >>> # define settings class as per pydantic documentation
    >>> class Settings(BaseSettings):
    ...     foobar: str = ""
    ...     baz: int = 42
    ...     class Config:
    ...         # define the load order as needed
    ...         @classmethod
    ...         def customise_sources(
    ...             cls,
    ...             init_settings,
    ...             env_settings,
    ...             file_secret_settings,
    ...         ):
    ...             return (
    ...                 init_settings,
    ...                 # the following returns a function that loads the temp_config file
    ...                 # this takes any predefined filename or list of filenames appropriate for your app
    ...                 get_settings_config_load_function(temp_config.name),
    ...                 env_settings,
    ...                 file_secret_settings,
    ...             )
    >>> my_settings = Settings()
    >>> my_settings.foobar
    'johndoe'
    >>> my_settings.baz
    42
    >>> rmtree(dirpath)

    ```
    """
    return partial(
        _settings_config_load,
        file_path=file_path,
        data_type=data_type,
        encoding=encoding,
        error_handling=error_handling,
    )
