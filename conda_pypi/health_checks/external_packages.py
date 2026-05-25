# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Health check: Report packages not installed by conda"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from conda.api import SubdirData
from conda.base.constants import OK_MARK, X_MARK
from conda.base.context import context
from conda.cli.install import reinstall_packages
from conda.common.constants import NULL
from conda.core.prefix_data import PrefixData
from conda.models.records import PrefixRecord

from conda_pypi.name_mapping import pypi_to_conda_name

if TYPE_CHECKING:
    from argparse import Namespace

    from conda.plugins.types import ConfirmCallback


def find_external_packages(prefix: str) -> list[PrefixRecord]:
    """Identify packages that were not installed by conda."""
    prefix_data = PrefixData(prefix, interoperability=True)
    external_packages = prefix_data.get_python_packages()
    return external_packages


def print_external_packages(prefix: str, verbose: bool) -> None:
    """Print packages not installed by conda."""
    external_packages = find_external_packages(prefix)
    if not external_packages:
        print(f"{OK_MARK} No external packages found.\n")
    else:
        print(f"{X_MARK} These packages are not installed by conda:\n")
        for package in external_packages:
            print(package.name, package.version)
        print("")


def conda_has_package(name: str) -> bool:
    """Check if a package with the given name exists in conda channels."""
    result = SubdirData.query_all(name)
    return bool(result)


def build_migration_plan(packages) -> list:
    """Determine which packages can be safely migrated to conda."""
    safe_pkgs_conda_names = []
    safe_pkgs_pypi = []

    for pkg in packages:
        # name = pkg.name.replace("_", "-")
        conda_name = pypi_to_conda_name(pkg.name)

        # check if conda can install it
        if conda_has_package(conda_name):
            safe_pkgs_conda_names.append(conda_name)
            if pkg.name != conda_name:
                print(
                    f"Note: '{pkg.name}' will be reinstalled as '{conda_name}' from conda channels.\n"
                )
            safe_pkgs_pypi.append(pkg)

    return safe_pkgs_conda_names, safe_pkgs_pypi


def clean_up_stale_files(prefix: str, pkg_name: str, pkg_version: str) -> None:
    """Remove dist-info directories left behind by pip after migration."""

    lib = Path(prefix) / "lib"

    site_packages_candidates = list(lib.glob("python*/site-packages"))
    if not site_packages_candidates:
        raise FileNotFoundError(f"No site-packages found in {lib}")

    # there is only one site-packages directory in a conda env
    site_packages_dir = site_packages_candidates[0]

    # respect dist-info naming convention, replace dashes with underscores in package names
    pkg_name = pkg_name.replace("-", "_")
    pattern = f"{pkg_name}-{pkg_version}.dist-info"

    for path in site_packages_dir.glob(pattern):
        print(f"Removing stale file: {path}")
        shutil.rmtree(path)


def migrate_to_conda(prefix: str, args: Namespace, confirm: ConfirmCallback) -> None:
    """Migrate pip-installed packages to conda."""

    if prefix == context.root_prefix:
        print("Cannot migrate packages in the base environment.")
        return 0

    external_packages = find_external_packages(prefix)

    if not external_packages:
        print("No external packages found.")
        return 0

    safe_pkgs_conda_names, safe_pkgs_pypi_names = build_migration_plan(external_packages)

    if not safe_pkgs_conda_names:
        print("No safe packages to migrate.")
        return 0

    print()
    confirm("Reinstall these packages with conda?")

    args.use_local = False
    args.file = []
    args.repodata_fns = ("repodata.json",)
    args.update_modifier = NULL

    reinstall_packages(args, safe_pkgs_conda_names, force_reinstall=True)

    for pkg in safe_pkgs_pypi_names:
        clean_up_stale_files(prefix, pkg.name, pkg.version)
