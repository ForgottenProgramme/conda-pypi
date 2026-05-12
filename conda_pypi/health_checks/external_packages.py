# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Health check: Report packages not installed by conda"""

from __future__ import annotations

from typing import TYPE_CHECKING

from conda_pypi.name_mapping import pypi_to_conda_name, conda_to_pypi_name

from conda.env.pip_util import pip_subprocess
from conda.common.constants import NULL
from conda.base.constants import OK_MARK, X_MARK
from conda.base.context import context
from conda.cli.install import reinstall_packages
from conda.core.prefix_data import PrefixData
from conda.plugins import hookimpl
from conda.plugins.types import CondaHealthCheck
from conda.api import SubdirData

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Iterable

    from conda.plugins.types import ConfirmCallback


def find_external_packages(prefix: str) -> list[PrefixData]:
    prefix_data = PrefixData(prefix, interoperability=True)
    external_packages = prefix_data.get_python_packages()
    return external_packages


def print_external_packages(prefix: str, verbose: bool) -> None:

    external_packages = find_external_packages(prefix)
    if not external_packages:
        print(f"{OK_MARK} No external packages found.\n")
    else:
        print(f"{X_MARK} These packages are not installed by conda:\n")
        for package in external_packages:
            print(package.name)
        print("")


def conda_has_package(name: str) -> bool:
    result = SubdirData.query_all(name)
    return bool(result)


def build_migration_plan(packages):
    safe_pkgs_conda_names = []
    external_only = []
    safe_pkgs_pypi_names=[]

    for pkg in packages:
        name = pkg.name.replace("_", "-")

        conda_name = pypi_to_conda_name(pkg.name)
        if conda_name != name:
            print(f"Note: '{name}' will be reinstalled as '{conda_name}' from conda channels.\n")
    

        # check if conda can install it
        if conda_has_package(conda_name):
            safe_pkgs_conda_names.append(conda_name)
            safe_pkgs_pypi_names.append(name)
        else:
            external_only.append(name)

    return safe_pkgs_conda_names, external_only, safe_pkgs_pypi_names


def migrate_to_pypi(prefix: str, args: Namespace, confirm: ConfirmCallback) -> int:

    if prefix == context.root_prefix:
        print("Cannot migrate packages in the base environment.")
        return 0

    external_packages = find_external_packages(prefix)

    if not external_packages:
        print("No external packages found.")
        return 0

    safe_pkgs_conda_names, external_only, safe_pkgs_pypi_names = build_migration_plan(external_packages)

    if not safe_pkgs_conda_names:
        print("No safe packages to migrate.")
        return 0

    print(f"Found {len(safe_pkgs_conda_names)} package(s) safe to migrate:")
    for name in sorted(safe_pkgs_conda_names):
        print(f"  {name}")

    print()
    confirm("Reinstall these packages with conda?")

    for package in safe_pkgs_pypi_names:
        stdout, stderr = pip_subprocess(["uninstall", package, "-y"], prefix, cwd=None)

        print(f"Uninstalling {package}...")
        print(stdout)

        if stderr:
            print("Error:", stderr)

    # args required by reinstall_packages (defined in conda)
    args.use_local = False
    args.file = []
    args.repodata_fns = ("repodata.json",)
    args.update_modifier = NULL

    return reinstall_packages(args, safe_pkgs_conda_names, force_reinstall=True)
