
from os import PathLike
from pathlib import Path
from typing import Union, AnyStr, MutableMapping, Any

import yaml

from .config_data_types import ConfigDataTypes
from .config_exceptions import DictLoadError
from ..utility.typing import Buffer



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
            
        # TODO
        # Improvement suggestions
        # if hasattr(exc, 'problem_mark'):
        #     if exc.context != None:
        #         print ('  parser says\n' + str(exc.problem_mark) + '\n  ' +
        #             str(exc.problem) + ' ' + str(exc.context) +
        #             '\nPlease correct data and retry.')
        #     else:
        #         print ('  parser says\n' + str(exc.problem_mark) + '\n  ' +
        #             str(exc.problem) + '\nPlease correct data and retry.')
        # #####
        # if hasattr(err, 'problem_mark'):
        #     mark = getattr(err, 'problem_mark')
        #     problem = getattr(err, 'problem')
        #     message = f"Could not read {label} {filename}:"
        #     message += "\n" + display_err_in_file(filename, mark.line, mark.column, problem)
        # elif hasattr(err, 'problem'):
        #     problem = getattr(err, 'problem')
        #     message = f"Could not read {label} {filename}: {problem}"
        # else:
        #     message = f"Could not read {label} {filename}: YAML Error"

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

