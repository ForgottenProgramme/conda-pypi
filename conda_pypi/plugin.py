from __future__ import annotations

from conda.common.configuration import PrimitiveParameter
from conda.plugins import hookimpl
from conda.plugins.types import (
    CondaHealthCheck,
    CondaPackageExtractor,
    CondaPostCommand,
    CondaSetting,
    CondaSubcommand,
)

from conda_pypi import cli
from conda_pypi.health_checks.external_packages import migrate_to_conda, print_external_packages
from conda_pypi.main import notify_externally_managed_future
from conda_pypi.package_extractors.whl import extract_whl_as_conda_pkg


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
        name="conda-pypi-notify-externally-managed-future",
        action=notify_externally_managed_future,
        run_for={"install", "create", "env_create"},
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


@hookimpl
def conda_settings():
    yield CondaSetting(
        name="conda_pypi_pip_warning",
        description="Enable or disable the conda-pypi beta tip shown when pip is present",
        parameter=PrimitiveParameter(True),
    )
