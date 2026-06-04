# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for external packages health check."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from pathlib import PurePosixPath, Path

from conda_pypi.health_checks.external_packages import find_external_packages, conda_has_package, print_external_packages, build_migration_plan, normalize_conda_file_paths, get_conda_owned_paths, find_python_metadata_directories, clean_up_stale_files, clean_up_stale_files
from conda.base.constants import OK_MARK, X_MARK


py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"

if TYPE_CHECKING:
    from pathlib import Path

    from conda.testing.fixtures import PipCLIFixture, TmpEnvFixture


def test_no_external_packages(tmp_env: TmpEnvFixture):
    with tmp_env() as prefix:
        assert find_external_packages(prefix) == []


def test_external_packages(tmp_env: TmpEnvFixture, pip_cli: PipCLIFixture):
    """Test detection of external packages after installing with pip."""
    with tmp_env(f"python={py_ver}", "pip") as prefix:
        stdout, stderr, code = pip_cli("install", "requests", prefix=prefix)
        assert code == 0
        packages = find_external_packages(prefix)
        assert packages != []

        names=[]
        for pkg in packages:
            names.append(pkg.name)

        assert "requests" in names


def test_conda_has_package():
    """Test detection of packages available in conda channels."""
    assert conda_has_package("requests") == True


def test_conda_does_not_have_package():
    """Test that non-existent packages return False."""
    assert conda_has_package("this_package_definitely_does_not_exist_xyz_123") == False


def test_print_external_packages_output(tmp_env: TmpEnvFixture, pip_cli: PipCLIFixture, capsys):
    """Test the printed output format."""
    with tmp_env(f"python={py_ver}", "pip") as prefix:
        stdout, stderr, code = pip_cli("install", "requests", prefix=prefix)
        assert code == 0
        print_external_packages(prefix, verbose=False)
        captured = capsys.readouterr()

        assert X_MARK in captured.out


def test_print_external_packages_no_packages(tmp_env: TmpEnvFixture, capsys):
    """Test output when no external packages found."""
    with tmp_env() as prefix:
        print_external_packages(prefix, verbose=False)
        captured = capsys.readouterr()
        
        assert OK_MARK in captured.out


def test_build_migration_plan_safe_packages(tmp_env: TmpEnvFixture, pip_cli: PipCLIFixture):
    """Test building a migration plan for packages available in conda."""
    with tmp_env(f"python={py_ver}", "pip") as prefix:
        # Install a real package that exists in both pip and conda
        pip_cli("install", "requests", prefix=prefix)
        
        packages = find_external_packages(prefix)
        conda_names, pypi_names = build_migration_plan(packages)
        
        # requests should be found in conda
        assert len(conda_names) > 0
        assert len(pypi_names) == len(packages)


def test_normalize_conda_file_paths():
    """Test that backslashes are converted to forward slashes."""
    # Create a mock PrefixRecord with Windows-style paths
    from unittest.mock import Mock
    
    mock_record = Mock()
    mock_record.files = [
        "Lib\\site-packages\\package\\__init__.py",
        "Lib/site-packages/package/module.py"
    ]
    paths = normalize_conda_file_paths(mock_record)
    assert all("/" in str(p) for p in paths)
    assert "\\" not in str(paths)


def test_get_conda_owned_paths(tmp_env: TmpEnvFixture):
    """Test retrieval of conda-owned file paths."""
    with tmp_env("numpy") as prefix:
        owned_paths = get_conda_owned_paths(prefix)
        
        assert len(owned_paths) > 0
        # verify structure is PurePosixPath
        assert all(isinstance(p, PurePosixPath) for p in owned_paths)


def test_clean_up_stale_files_removes_unowned_metadata(tmp_env: TmpEnvFixture, pip_cli: PipCLIFixture):
    """Test removal of stale metadata directories."""
    with tmp_env(f"python={py_ver}", "pip") as prefix:
        pip_cli("install", "requests", prefix=prefix)
        
        packages = find_external_packages(prefix)
        conda_owned = get_conda_owned_paths(prefix)
        
        # Find metadata dirs before cleanup
        metadata_dirs_before = []
        for pkg in packages:
            metadata_dirs_before.extend(find_python_metadata_directories(pkg))
        
        for pkg in packages:
            clean_up_stale_files(prefix, pkg, conda_owned)
        
        # Verify those specific directories are gone
        prefix_path = Path(prefix)
        for metadata_dir in metadata_dirs_before:
            path = prefix_path / metadata_dir
            assert not path.exists(), f"Stale metadata directory {path} should have been removed"