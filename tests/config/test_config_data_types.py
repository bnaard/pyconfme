import pytest
from pyconfme.config.config_data_types import ConfigDataTypes


def test_config_data_types():
    assert set(ConfigDataTypes.allowed_names()) == set(["json", "toml", "yaml", "infer", "unknown"])
