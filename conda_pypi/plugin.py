from __future__ import annotations

from conda.common.configuration import PrimitiveParameter
from conda.plugins import hookimpl
from conda.plugins.types import (
    CondaPackageExtractor,
    CondaPostCommand,
    CondaSetting,
    CondaSubcommand,
    CondaHealthCheck,
)

from conda_pypi import cli, post_command
from conda_pypi.main import ensure_target_env_has_externally_managed
from conda_pypi.package_extractors.whl import extract_whl_as_conda_pkg
from conda_pypi.health_checks.external_packages import print_external_packages, migrate_to_conda


@hookimpl
def conda_subcommands():
    yield CondaSubcommand(
        name="pypi",
        action=cli.main.execute,
        configure_parser=cli.main.configure_parser,
        summary="Install PyPI packages as conda packages",
    )


@hookimpl
def conda_post_commands():
    yield CondaPostCommand(
        name="conda-pypi-ensure-target-env-has-externally-managed",
        action=ensure_target_env_has_externally_managed,
        run_for={"install", "create", "update", "remove"},
    )
    yield CondaPostCommand(
        name="conda-pypi-post-install-create",
        action=post_command.install.post_command,
        run_for={"install", "create"},
    )


@hookimpl
def conda_package_extractors():
    yield CondaPackageExtractor(
        name="wheel-package",
        extensions=[".whl"],
        extract=extract_whl_as_conda_pkg,
    )


@hookimpl
def conda_health_checks():
    yield CondaHealthCheck(
        name="external-packages",
        action=print_external_packages,
        fixer=migrate_to_conda,
        summary="List packages not installed by conda.",
    )
def conda_settings():
    yield CondaSetting(
        name="conda_pypi_pip_warning",
        description="Enable or disable the warning about using pip in conda environents",
        parameter=PrimitiveParameter(True),
    )
