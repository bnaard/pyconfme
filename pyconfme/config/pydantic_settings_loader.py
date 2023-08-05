
import sys
from pathlib import Path
from functools import partial
from typing import Any, Dict, Callable, cast, Union, Sequence, AnyStr

from pydantic import BaseSettings

from .config_data_types import ConfigDataTypes
from .config_exceptions import DictLoadError
from .config_loader import load_dict_from_file  # pyright: ignore[reportMissingImports]
from ..utility.type_helpers import FilePathOrBuffer
from ..utility.dict_deep_update import dict_deep_update


# TODO
# Introduce enum for error handling instead of string comparison

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


# TODO
# Rewrite example in comment according to new pydantic documentation https://docs.pydantic.dev/latest/usage/pydantic_settings/#customise-settings-sources

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
