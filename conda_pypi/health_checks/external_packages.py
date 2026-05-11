# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Health check: Report packages not installed by conda"""

from __future__ import annotations

from typing import TYPE_CHECKING

from conda_pypi.name_mapping import pypi_to_conda_name

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
    safe = []
    external_only = []

    for pkg in packages:
        name = pkg.name.replace("_", "-")

        conda_name = pypi_to_conda_name(pkg.name)
        if conda_name != name:
            print(f"Note: '{name}' will be reinstalled as '{conda_name}' from conda channels.\n")
    

        # check if conda can install it
        if conda_has_package(conda_name):
            safe.append(conda_name)
        else:
            external_only.append(name)

    return safe, external_only


def migrate_to_pypi(prefix: str, args: Namespace, confirm: ConfirmCallback) -> int:

    if prefix == context.root_prefix:
        print("Cannot migrate packages in the base environment.")
        return 0

    external_packages = find_external_packages(prefix)

    if not external_packages:
        print("No external packages found.")
        return 0

    safe_packages, external_only = build_migration_plan(external_packages)

    if not safe_packages:
        print("No safe packages to migrate.")
        return 0

    print(f"Found {len(safe_packages)} package(s) safe to migrate:")
    for name in sorted(safe_packages):
        print(f"  {name}")

    print()
    confirm("Reinstall these packages with conda?")

    args.use_local = False
    args.file = []
    args.repodata_fns = ("repodata.json",)
    args.update_modifier = NULL

    return reinstall_packages(args, safe_packages, force_reinstall=True)
