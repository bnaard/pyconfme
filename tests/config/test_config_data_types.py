import pytest
from pyconfme.config.config_data_types import ConfigDataTypes


def test_config_data_types():
    try:
        yaml = ConfigDataTypes.yaml
    except Exception as e:
        pytest.fail( f"Testing ConfigDataTypes.yaml raised exception {e}.")

    try:
        json = ConfigDataTypes.json
    except Exception as e:
        pytest.fail( f"Testing ConfigDataTypes.json raised exception {e}.")

    try:
        yaml = ConfigDataTypes.toml
    except Exception as e:
        pytest.fail( f"Testing ConfigDataTypes.toml raised exception {e}.")

    try:
        yaml = ConfigDataTypes.infer
    except Exception as e:
        pytest.fail( f"Testing ConfigDataTypes.infer raised exception {e}.")

    try:
        yaml = ConfigDataTypes.unknown
    except Exception as e:
        pytest.fail( f"Testing ConfigDataTypes.unknown raised exception {e}.")



    # assert set(ConfigDataTypes.allowed_names()) == set(["json", "toml", "yaml", "infer", "unknown"])
