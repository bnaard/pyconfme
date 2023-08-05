from os import chmod
import pytest
from pathlib import Path
from io import StringIO
from pydantic import BaseSettings
from tempfile import mkdtemp
from shutil import rmtree
import sys


from pyconfme.config.config_data_types import ConfigDataTypes
from pyconfme.config.config_exceptions import DictLoadError
from pyconfme.config.pydantic_settings_loader import (
    _settings_config_load,
    get_settings_config_load_function,
)


class DummyRunserverSettings(BaseSettings):
    port: int = 1234


class DummySettings(BaseSettings):
    runserver: DummyRunserverSettings = DummyRunserverSettings()


@pytest.fixture
def dummy_settings():
    return DummySettings()


def _inner_test(
    dummy_settings,
    file_path,
    expected_exception,
    data_type,
    encoding,
    error_handling,
    resulting_dict,
    function_in_test = _settings_config_load
):
    if expected_exception is None:
        assert (
            function_in_test(
                settings=dummy_settings,
                file_path=file_path,
                data_type=data_type,
                encoding=encoding,
                error_handling=error_handling,
            )
            == resulting_dict
        )
        if not isinstance(file_path, list):
            if isinstance(file_path, tuple):
                file_path = list(file_path)
            else:
                file_path = [file_path]
        for afile_path in file_path:
            if not isinstance(afile_path, Path) and afile_path is not None:
                if resulting_dict is None:
                    assert afile_path.tell() == 0
                afile_path.close()
    else:
        with pytest.raises(expected_exception):
            assert (
                function_in_test(
                    settings=dummy_settings,
                    file_path=file_path,
                    data_type=data_type,
                    encoding=encoding,
                    error_handling=error_handling,
                )
                == resulting_dict
            )


@pytest.mark.parametrize(
    "file_path, expected_exception, data_type, encoding, error_handling,"
    " resulting_dict",
    [
        (Path("example_cfgX.json"), None, None, None, None, {}),
        (Path("example_cfgX.json"), None, None, None, "propagate", {}),
        (Path("example_cfgX.json"), None, None, None, "abort", {}),
        (Path("example_cfgX.json"), None, None, None, "ignore", {}),
        (Path("example_cfgX.json"), ValueError, None, None, "foobar", {}),
        (Path("example_cfgX.json"), ValueError, None, None, 42, {}),
        (None, ValueError, None, None, "propagate", {}),
        (None, None, None, None, "ignore", {}),
        (None, SystemExit, None, None, "abort", {}),
        (Path("tests/config"), None, None, None, None, {}),
        (
            Path("tests/config/example_malformed_cfg3.json"),
            DictLoadError,
            None,
            None,
            None,
            None,
        ),
        (
            open("tests/config/example_malformed_cfg3.json"),
            DictLoadError,
            None,
            None,
            None,
            None,
        ),
        (
            Path("tests/config/example_malformed_cfg3.json"),
            DictLoadError,
            ConfigDataTypes.json,
            None,
            None,
            {},
        ),
        (
            Path("tests/config/example_cfg3.json"),
            None,
            None,
            None,
            None,
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            Path("tests/config/example_cfg3.json"),
            None,
            ConfigDataTypes.json,
            None,
            None,
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            open("tests/config/example_cfg3.json", "r+b"),
            None,
            ConfigDataTypes.json,
            None,
            None,
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            StringIO('{"main": "started", "runserver": { "nested_list": [42, 96]}}'),
            None,
            ConfigDataTypes.json,
            None,
            None,
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            StringIO('{"main": "started", "runserver" = { "nested_list": [42, 96]}}'),
            DictLoadError,
            ConfigDataTypes.json,
            None,
            None,
            {},
        ),
        (
            StringIO('{"main": "started", "runserver" = { "nested_list": [42, 96]}}'),
            DictLoadError,
            ConfigDataTypes.toml,
            None,
            None,
            None,
        ),
        (
            StringIO('{"main": "started", "runserver" = { "nested_list": [42, 96]}}'),
            DictLoadError,
            ConfigDataTypes.toml,
            None,
            None,
            None,
        ),
        (42, DictLoadError, None, None, None, None),
        (
            StringIO('{"main": "started", "runserver" = { "nested_list": [42, 96]}}'),
            SystemExit,
            ConfigDataTypes.toml,
            None,
            "abort",
            None,
        ),
        (
            [
                Path("tests/config/example_cfg1.yaml"),
                Path("tests/config/example_cfg3.json"),
            ],
            None,
            None,
            None,
            None,
            {"main": "started", "runserver": {"nested_list": [42, 96], "port": 3333}},
        ),
        (
            (
                Path("tests/config/example_cfg1.yaml"),
                Path("tests/config/example_cfg3.json"),
            ),
            None,
            None,
            None,
            None,
            {"main": "started", "runserver": {"nested_list": [42, 96], "port": 3333}},
        ),
    ],
)
def test__settings_config_load(
    dummy_settings,
    file_path,
    expected_exception,
    data_type,
    encoding,
    error_handling,
    resulting_dict,
):
    _inner_test(
        dummy_settings=dummy_settings,
        file_path=file_path,
        expected_exception=expected_exception,
        data_type=data_type,
        encoding=encoding,
        error_handling=error_handling,
        resulting_dict=resulting_dict,
    )


@pytest.fixture
def temp_file_path():
    dirpath = mkdtemp()
    temp_config_name = Path(dirpath) / "config.ini"
    temp_config = open(temp_config_name, "wt")
    _ = temp_config.write('foobar = "johndoe"')
    temp_config.close()
    chmod(temp_config_name, 0o222)
    yield temp_config_name
    rmtree(dirpath)


@pytest.mark.parametrize(
    "expected_exception, data_type, encoding, error_handling, resulting_dict",
    [
        (SystemExit, None, None, "abort", {}),
        (IOError, None, None, "propagate", {}),
        (None, None, None, "ignore", {}),
    ],
)
def test__settings_config_load_permission_error(
    dummy_settings,
    temp_file_path,
    expected_exception,
    data_type,
    encoding,
    error_handling,
    resulting_dict,
):
    if "win" in sys.platform:
        return True
    _inner_test(
        dummy_settings=dummy_settings,
        file_path=temp_file_path,
        expected_exception=expected_exception,
        data_type=data_type,
        encoding=encoding,
        error_handling=error_handling,
        resulting_dict=resulting_dict,
    )


@pytest.mark.parametrize(
    "file_path, expected_exception, data_type, encoding, error_handling,"
    " resulting_dict",
    [
        (
            Path("tests/config/example_cfg3.json"),
            None,
            ConfigDataTypes.json,
            None,
            None,
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
    ]
)
def test__get_settings_load_function(
    dummy_settings,
    file_path,
    expected_exception,
    data_type,
    encoding,
    error_handling,
    resulting_dict,
):
    f= get_settings_config_load_function(file_path)

    _inner_test(
        dummy_settings=dummy_settings,
        file_path=file_path,
        expected_exception=expected_exception,
        data_type=data_type,
        encoding=encoding,
        error_handling=error_handling,
        resulting_dict=resulting_dict,
        function_in_test=f,
    )
