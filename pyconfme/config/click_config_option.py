import click
from pydantic import BaseSettings, ValidationError
from typing import Sequence, TypeVar, Dict, cast
from pathlib import Path
from functools import partial


from ..utility.dict_deep_update import dict_deep_update
from .config_file_loaders import DictLoadError, load_dict_from_file
# from .config_data_types import ConfigDataTypes

SettingsClassType = TypeVar("SettingsClassType", bound=BaseSettings)


def _validate(
    ctx: click.Context,
    param,
    value,
    settings_obj: BaseSettings,
    settings_class_type: SettingsClassType,
):
    if not value:
        return list()
    if not isinstance(value, Sequence):
        value = [value]
    config_map = {}
    for config_file in value:
        config_file = Path(config_file).resolve()
        try:
            config_map[str(config_file)] = load_dict_from_file(config_file)
        except DictLoadError as e:
            click.echo(
                f"{e.message}\nContext:\n{e.document}\nPosition = {e.position},"
                f" line number = {e.line_number}, column_number = {e.column_number}"
            )
            ctx.abort()

    target_config_dict = settings_obj.dict()
    new_settings_obj: BaseSettings = None
    for config_file, config_dict in config_map.items():
        try:
            dict_deep_update(
                target_config_dict, cast(Dict[object, object], config_dict)
            )
        except RecursionError as e:
            click.echo(
                f"Error reading {config_file}.\nData structure depth exceeded.\n{e}"
            )
            ctx.abort()
        except ValueError as e:
            click.echo(f"{e}")
            ctx.abort()

        try:
            new_settings_obj = settings_class_type.parse_obj(target_config_dict)
        except ValidationError as e:
            click.echo(f"Validation error for config file {config_file}.\n{e}")
            ctx.abort()

    ctx.default_map = new_settings_obj.dict()
    return new_settings_obj


def click_config_option(
    settings_obj: BaseSettings,
    settings_class_type: SettingsClassType,
    click_obj=click,
    option_name: str = "config",
    option_short: str = "",
    **kw,
):
    """Decorator that provides an out-of-the box `--config`-option for click-commands. The options allows
    to provide one or more configuration files that are loaded at program invocation and read into a given
    pydantic settings class.

    Args:
        settings_obj: an object instantiated from a pydantic settings class
        settings_class_type: a class derived from pydantic settings class
        click_obj: the global click-module object managing the application
        option_name: name of the option on the commandline, defaults to `config`,
            | invoked on commandline with `--config=<path-to-config-file>`
        option_short_name: one-letter short-name, defaults to `c`. Eg. if `c` is given,
            | invoked on commandline with `-c <path-to-config-file>`
    Returns:
        click-option object
    Example:
    ```python
    >>> import click
    >>> from click.testing import CliRunner
    >>> from pydantic import BaseSettings
    >>> from pyconfme import click_config_option
    >>> from tempfile import mkdtemp
    >>> from shutil import rmtree
    >>> # create a temporary config file
    >>> dirpath = mkdtemp()
    >>> temp_config_name = Path(dirpath) / "config.ini"
    >>> temp_config = open(temp_config_name, "wt")
    >>> _ = temp_config.writelines(['debug = false\\n', 'port = 4242'])
    >>> temp_config.close()
    >>> class Settings(BaseSettings):
    ...     debug: bool = False
    ...     port: int = 1234
    >>> settings = Settings()
    >>> @click.command(context_settings=dict(default_map=settings.dict() ))
    ... @click_config_option(settings, Settings)
    ... @click.option('--debug/--no-debug', default=settings.debug, help="debug", type=bool, show_default=True)
    ... @click.pass_context
    ... def cli(ctx, config, debug):
    ...     click.echo(f'Config is {config.dict()}')
    ...     click.echo('Debug mode is %s' % ('on' if debug else 'off'))
    ...     click.echo(f'Context = {ctx.default_map}')
    >>> # Simulate calling the commandline app to show usage of config-option
    >>> runner = CliRunner()
    >>> result = runner.invoke(cli, ['--debug', '--config', str(temp_config_name) ])
    >>> print(result.stdout)
    Config is {'debug': False, 'port': 4242}
    Debug mode is on
    Context = {'debug': False, 'port': 4242}
    <BLANKLINE>
    >>> rmtree(dirpath)

    ```
    """

    option_kwargs = dict(
        help="Config file path for loading settings from file.",
        callback=partial(
            _validate,
            settings_obj=settings_obj,
            settings_class_type=settings_class_type,
        ),
        type=click.Path(exists=True, dir_okay=False, resolve_path=True),
        expose_value=True,
        is_eager=True,
        multiple=True,
    )
    option_kwargs.update(kw)
    option_short = (
        option_short.lstrip("-")
        if option_short.lstrip("-") != ""
        else f"{option_name[0]}"
    )
    option_name = option_name.lstrip("-")
    option = click_obj.option(f"--{option_name}", f"-{option_short}", **option_kwargs)
    return option
