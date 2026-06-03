# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for external packages health check."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from conda_pypi.health_checks.external_packages import find_external_packages, conda_has_package, print_external_packages

py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"

if TYPE_CHECKING:
    from pathlib import Path

    from conda.testing.fixtures import PipCLIFixture, TmpEnvFixture


def test_no_external_packages(tmp_env: TmpEnvFixture):
    with tmp_env() as prefix:
        assert find_external_packages(prefix) == []


def test_external_packages(tmp_env: TmpEnvFixture, pip_cli: PipCLIFixture, wheelhouse: Path):
    with tmp_env(f"python={py_ver}", "pip") as prefix:
        wheel_path = wheelhouse / "small_python_package-1.0.0-py3-none-any.whl"
        _, _, _ = pip_cli("install", wheel_path, prefix=prefix)

        packages = find_external_packages(prefix)

        assert packages != []
        assert "small-python-package" == packages[0].name


def test_conda_has_package_existing_package():
    """Test detection of packages available in conda channels."""
    assert conda_has_package("numpy") is True


def test_conda_has_package_nonexistent():
    """Test that non-existent packages return False."""
    assert conda_has_package("this_package_definitely_does_not_exist_xyz_123") is False


def test_print_external_packages_output(tmp_env: TmpEnvFixture, pip_cli: PipCLIFixture, wheelhouse: Path, capsys):
    """Test the printed output format."""
    with tmp_env(f"python={py_ver}", "pip") as prefix:
        wheel_path = wheelhouse / "small_python_package-1.0.0-py3-none-any.whl"
        pip_cli("install", wheel_path, prefix=prefix)
        print_external_packages(prefix, verbose=False)
        captured = capsys.readouterr()

        assert "X_MARK" in captured.out


def test_print_external_packages_no_packages(tmp_env: TmpEnvFixture, capsys):
    """Test output when no external packages found."""
    with tmp_env() as prefix:
        print_external_packages(prefix, verbose=False)
        captured = capsys.readouterr()
        
        assert "OK_MARK" in captured.out
