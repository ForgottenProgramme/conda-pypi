"""
Tests for the `conda pypi index` subcommand.
"""

from pathlib import Path

import pytest

from conda_pypi.cli.index import validate_dir_and_return_whl_files

here = Path(__file__).parent.parent


def test_validate_dir_not_a_directory(tmp_path):
    not_a_dir = tmp_path / "file.txt"
    with pytest.raises(Exception):
        validate_dir_and_return_whl_files(not_a_dir)


def test_validate_dir_empty(tmp_path):
    with pytest.raises(SystemExit):
        validate_dir_and_return_whl_files(tmp_path)


def test_validate_dir_no_wheels(tmp_path):
    (tmp_path / "somedir").mkdir()
    with pytest.raises(SystemExit):
        validate_dir_and_return_whl_files(tmp_path)


def test_validate_dir_returns_wheels():
    result = validate_dir_and_return_whl_files(here / "pypi_local_index")
    assert len(result) > 1
    assert any(wheel.name == "demo_package-0.1.0-py3-none-any.whl" for wheel in result)
