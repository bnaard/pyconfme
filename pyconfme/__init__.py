"""pyconfme, Configuration options with multiple config-files and command-line made easy when creating applications with Python Click. """

__version__= "0.0.1"

from .config.settings_doc import with_attrs_docs
from .config.config_data_types import ConfigDataTypes
from .config.config_loader import load_dict_from_file
from .config.pydantic_settings_loader import get_settings_config_load_function


# from .config.click_config_option import click_config_option
