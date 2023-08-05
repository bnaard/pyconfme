import pytest
from pathlib import Path
from hypothesis import given, strategies as st
from string import printable
from io import StringIO
import mmap
import os

from pyconfme.config.config_data_types import ConfigDataTypes
from pyconfme.config.config_exceptions import DictLoadError
from pyconfme.config.json_loader import _load_dict_from_json_stream_or_file
from pyconfme.config.toml_loader import _load_dict_from_toml_stream_or_file
from pyconfme.config.yaml_loader import _load_dict_from_yaml_stream_or_file
from pyconfme.config.config_loader import (
    _determine_config_file_type,
    load_dict_from_file,
)


@pytest.mark.parametrize(
    "file_path, resulting_type",
    [
        (Path("example_cfg1.yaml"), ConfigDataTypes.yaml),
        (Path("example_cfg2.toml"), ConfigDataTypes.toml),
        (Path("example_cfg3.json"), ConfigDataTypes.json),
        (Path("not_existing.jsn"), ConfigDataTypes.json),
        (Path("not_existing.ini"), ConfigDataTypes.toml),
        (Path("not_existing.yml"), ConfigDataTypes.yaml),
        (Path("not_existing.cfg"), ConfigDataTypes.toml),
        (Path("not_existing.config"), ConfigDataTypes.toml),
        (Path("not_existing.CoNfIg"), ConfigDataTypes.toml),
        (Path("not_existing.xyz"), ConfigDataTypes.unknown),
        (Path("not_existing"), ConfigDataTypes.unknown),
        ("not_existing.config", ConfigDataTypes.toml),
    ],
)
def test_determine_config_data_type(file_path, resulting_type):
    assert _determine_config_file_type(file_path) == resulting_type


# BUG 
# mmap.mmap returns OSError 22 on VSCode Devcontainers /Podman even if used as per documentation https://docs.python.org/3/library/mmap.html
# mmap'ed files are currently not tested  
def _get_mmap(file_path):
    f = open(file_path, "r+b")
    return f
#     return mmap.mmap(fileno=f.fileno(), length=os.fstat(f.fileno()).st_size, access=mmap.ACCESS_READ)  # https://bugs.python.org/issue40785


@pytest.mark.parametrize(
    "file_path, expected_exception, data_type, resulting_dict",
    [
        (Path("example_cfgX.json"), FileNotFoundError, None, {}),
        (Path("does_not_exist.unknown"), FileNotFoundError, None, {}),
        (Path("tests/config"), IsADirectoryError, None, {}),
        (Path("tests/config/example_malformed_cfg3.json"), None, None, None),
        (open("tests/config/example_malformed_cfg3.json"), None, None, None),
        (
            Path("tests/config/example_malformed_cfg3.json"),
            DictLoadError,
            ConfigDataTypes.json,
            {},
        ),
        (
            Path("tests/config/example_cfg3.json"),
            None,
            None,
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            Path("tests/config/example_cfg3.json"),
            None,
            ConfigDataTypes.json,
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            open("tests/config/example_cfg3.json"),
            None,
            ConfigDataTypes.json,
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            open("tests/config/example_cfg3.json", "r+b"),
            None,
            ConfigDataTypes.json,
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            _get_mmap("tests/config/example_cfg3.json"),
            None,
            ConfigDataTypes.json,
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            StringIO('{"main": "started", "runserver": { "nested_list": [42, 96]}}'),
            None,
            ConfigDataTypes.json,
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            StringIO('{"main": "started", "runserver" = { "nested_list": [42, 96]}}'),
            DictLoadError,
            ConfigDataTypes.json,
            {},
        ),
        (
            StringIO('{"main": "started", "runserver" = { "nested_list": [42, 96]}}'),
            None,
            ConfigDataTypes.toml,
            None,
        ),
        (42, DictLoadError, None, None),
    ],
)
def test_load_dict_from_json_stream_or_file(
    file_path, expected_exception, data_type, resulting_dict
):
    if expected_exception is None:
        if data_type is None:
            assert _load_dict_from_json_stream_or_file(file_path) == resulting_dict
        else:
            assert (
                _load_dict_from_json_stream_or_file(file_path, data_type)
                == resulting_dict
            )
            if not isinstance(file_path, Path):
                if resulting_dict is None:
                    assert file_path.tell() == 0
                file_path.close()
    else:
        with pytest.raises(expected_exception):
            if data_type is None:
                _ = _load_dict_from_json_stream_or_file(file_path)
            else:
                _ = _load_dict_from_json_stream_or_file(file_path, data_type)


@pytest.mark.parametrize(
    "file_path, expected_exception, data_type, resulting_dict",
    [
        (Path("example_cfgX.toml"), FileNotFoundError, None, {}),
        (Path("does_not_exist.unknown"), FileNotFoundError, None, {}),
        (Path("tests/config"), IsADirectoryError, None, {}),
        (Path("tests/config/example_malformed_cfg2.toml"), None, None, None),
        (open("tests/config/example_malformed_cfg2.toml"), None, None, None),
        (
            Path("tests/config/example_malformed_cfg2.toml"),
            DictLoadError,
            ConfigDataTypes.toml,
            {},
        ),
        (
            Path("tests/config/example_cfg2.toml"),
            None,
            None,
            {"runserver": {"user": "someone"}},
        ),
        (
            Path("tests/config/example_cfg2.toml"),
            None,
            ConfigDataTypes.toml,
            {"runserver": {"user": "someone"}},
        ),
        (
            open("tests/config/example_cfg2.toml"),
            None,
            ConfigDataTypes.toml,
            {"runserver": {"user": "someone"}},
        ),
        (
            open("tests/config/example_cfg2.toml", "r+b"),
            None,
            ConfigDataTypes.toml,
            {"runserver": {"user": "someone"}},
        ),
        (
            _get_mmap("tests/config/example_cfg2.toml"),
            None,
            ConfigDataTypes.toml,
            {"runserver": {"user": "someone"}},
        ),
        (
            StringIO('[runserver]\nuser = "someone"'),
            None,
            ConfigDataTypes.toml,
            {"runserver": {"user": "someone"}},
        ),
        (
            StringIO("[runserver]\nuser = someone"),
            DictLoadError,
            ConfigDataTypes.toml,
            {},
        ),
        (StringIO("[runserver]\nuser = someone"), None, ConfigDataTypes.json, None),
        (42, DictLoadError, None, None),
    ],
)
def test_load_dict_from_toml_stream_or_file(
    file_path, expected_exception, data_type, resulting_dict
):
    if expected_exception is None:
        if data_type is None:
            assert _load_dict_from_toml_stream_or_file(file_path) == resulting_dict
        else:
            assert (
                _load_dict_from_toml_stream_or_file(file_path, data_type)
                == resulting_dict
            )
            if not isinstance(file_path, Path):
                if resulting_dict is None:
                    assert file_path.tell() == 0
                file_path.close()
    else:
        with pytest.raises(expected_exception):
            if data_type is None:
                _ = _load_dict_from_toml_stream_or_file(file_path)
            else:
                _ = _load_dict_from_toml_stream_or_file(file_path, data_type)


@pytest.mark.parametrize(
    "file_path, expected_exception, data_type, resulting_dict",
    [
        (Path("example_cfgX.yaml"), FileNotFoundError, None, {}),
        (Path("does_not_exist.unknown"), FileNotFoundError, None, {}),
        (Path("tests/config"), IsADirectoryError, None, {}),
        (Path("tests/config/example_malformed_cfg1.yaml"), None, None, None),
        (open("tests/config/example_malformed_cfg1.yaml"), None, None, None),
        (
            Path("tests/config/example_malformed_cfg1.yaml"),
            DictLoadError,
            ConfigDataTypes.yaml,
            {},
        ),
        (
            Path("tests/config/example_cfg1.yaml"),
            None,
            None,
            {"runserver": {"port": 3333}},
        ),
        (
            Path("tests/config/example_cfg1.yaml"),
            None,
            ConfigDataTypes.yaml,
            {"runserver": {"port": 3333}},
        ),
        (
            open("tests/config/example_cfg1.yaml"),
            None,
            ConfigDataTypes.yaml,
            {"runserver": {"port": 3333}},
        ),
        (
            open("tests/config/example_cfg1.yaml", "r+b"),
            None,
            ConfigDataTypes.yaml,
            {"runserver": {"port": 3333}},
        ),
        (
            _get_mmap("tests/config/example_cfg1.yaml"),
            None,
            ConfigDataTypes.yaml,
            {"runserver": {"port": 3333}},
        ),
        (
            StringIO("runserver:\n    port: 3333"),
            None,
            ConfigDataTypes.yaml,
            {"runserver": {"port": 3333}},
        ),
        (
            StringIO("[runserver]\n    port: 3333"),
            DictLoadError,
            ConfigDataTypes.yaml,
            {},
        ),
        (StringIO("[runserver]\n    port: 3333"), None, ConfigDataTypes.json, None),
        (42, DictLoadError, None, None),
    ],
)
def test_load_dict_from_yaml_stream_or_file(
    file_path, expected_exception, data_type, resulting_dict
):
    if expected_exception is None:
        if data_type is None:
            assert _load_dict_from_yaml_stream_or_file(file_path) == resulting_dict
        else:
            assert (
                _load_dict_from_yaml_stream_or_file(file_path, data_type)
                == resulting_dict
            )
            if not isinstance(file_path, Path):
                if resulting_dict is None:
                    assert file_path.tell() == 0
                file_path.close()
    else:
        with pytest.raises(expected_exception):
            if data_type is None:
                _ = _load_dict_from_yaml_stream_or_file(file_path)
            else:
                _ = _load_dict_from_yaml_stream_or_file(file_path, data_type)


@pytest.mark.parametrize(
    "file_path, expected_exception, data_type, encoding, resulting_dict",
    [
        (None, ValueError, None, "utf-8", {}),
        (Path("example_cfg1.yaml"), FileNotFoundError, None, "utf-8", {}),
        (Path("does_not_exist.unknown"), FileNotFoundError, None, "utf-8", {}),
        (Path("tests/config"), IsADirectoryError, None, "utf-8", {}),
        (
            Path("tests/config/example_malformed_cfg1.yaml"),
            DictLoadError,
            None,
            "utf-8",
            {},
        ),
        (
            Path("tests/config/example_malformed_cfg2.toml"),
            DictLoadError,
            None,
            "utf-8",
            {},
        ),
        (
            Path("tests/config/example_malformed_cfg3.json"),
            DictLoadError,
            None,
            "utf-8",
            {},
        ),
        (
            "tests/config/example_cfg1.yaml",
            None,
            None,
            "utf-8",
            {"runserver": {"port": 3333}},
        ),
        (
            Path("tests/config/example_cfg1.yaml"),
            None,
            None,
            "utf-8",
            {"runserver": {"port": 3333}},
        ),
        (
            Path("tests/config/example_cfg1.yaml"),
            None,
            ConfigDataTypes.yaml,
            "utf-8",
            {"runserver": {"port": 3333}},
        ),
        (
            Path("tests/config/example_cfg2.toml"),
            None,
            None,
            "utf-8",
            {"runserver": {"user": "someone"}},
        ),
        (
            Path("tests/config/example_cfg2.toml"),
            None,
            ConfigDataTypes.toml,
            "utf-8",
            {"runserver": {"user": "someone"}},
        ),
        (
            Path("tests/config/example_cfg3.json"),
            None,
            None,
            "utf-8",
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            Path("tests/config/example_cfg3.json"),
            None,
            ConfigDataTypes.json,
            "utf-8",
            {"main": "started", "runserver": {"nested_list": [42, 96]}},
        ),
        (
            Path("tests/config/example_cfg1.yaml"),
            None,
            ConfigDataTypes.infer,
            "utf-8",
            {"runserver": {"port": 3333}},
        ),
        (
            Path("tests/config/example_cfg1.yaml"),
            None,
            ConfigDataTypes.unknown,
            "utf-8",
            {"runserver": {"port": 3333}},
        ),
        (
            open("tests/config/example_cfg1.yaml", "r+b"),
            None,
            ConfigDataTypes.yaml,
            "utf-8",
            {"runserver": {"port": 3333}},
        ),
        (
            open("tests/config/example_cfg1.yaml", "r+b"),
            None,
            ConfigDataTypes.yaml,
            "utf-16",
            {"runserver": {"port": 3333}},
        ),
        (
            Path("tests/config/example_cfg1.yaml"),
            UnicodeError,
            None,
            "utf-16",
            {"runserver": {"port": 3333}},
        ),
        (
            Path("tests/config/example_cfg1.yaml"),
            None,
            None,
            None,
            {"runserver": {"port": 3333}},
        ),
        (
            Path("tests/config/example_cfg4.ini"),
            None,
            ConfigDataTypes.toml,
            "utf-8",
            {"debug": False, "port": 4242 },
        ),
        (
            Path("tests/config/example_malformed_cfg4.ini"),
            DictLoadError,
            ConfigDataTypes.toml,
            "utf-8",
            {"debug": False, "port": 4242 },
        ),
        (
            Path("tests/config/example_malformed_cfg4.ini"),
            DictLoadError,
            ConfigDataTypes.infer,
            "utf-8",
            {"debug": False, "port": 4242 },
        ),
    ],
)
def test_load_dict_from_file(
    file_path, expected_exception, data_type, encoding, resulting_dict
):
    if expected_exception is None:
        if data_type is None:
            assert load_dict_from_file(file_path, encoding=encoding) == resulting_dict
        else:
            assert (
                load_dict_from_file(file_path, data_type, encoding=encoding)
                == resulting_dict
            )
    else:
        with pytest.raises(expected_exception):
            if data_type is None:
                _ = load_dict_from_file(file_path, encoding=encoding)
            else:
                _ = load_dict_from_file(file_path, data_type, encoding=encoding)


def test_load_dict_from_file_exceeding_maxfilesize():
    with pytest.raises(ValueError):
        _ = load_dict_from_file(Path("tests/config/example_cfg1.yaml"), max_file_size=1)


@st.composite
def fspath_strategy(draw, path_elements=st.text(printable)):
    count_path_elements = draw(st.integers(min_value=0, max_value=5))
    path = Path()
    for _ in range(count_path_elements):
        path = path / Path(draw(path_elements))
    return Path(path)


@given(
    file_path=fspath_strategy(),
    data_type=st.sampled_from([el for el in ConfigDataTypes]),
)
def test_fuzzy_load_dict_from_file(file_path, data_type):
    with pytest.raises((FileNotFoundError, IsADirectoryError)):
        _ = load_dict_from_file(file_path, data_type)
