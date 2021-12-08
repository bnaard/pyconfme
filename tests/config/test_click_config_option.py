from os import chmod
import pytest
from pathlib import Path
from io import StringIO
from pydantic import BaseSettings
from tempfile import mkdtemp
from shutil import rmtree
import sys


from pyconfme.config.config_data_types import ConfigDataTypes
from pyconfme.config.click_config_option import (
    click_config_option,
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
    function_in_test = click_config_option
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
