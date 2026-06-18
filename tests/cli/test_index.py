"""
Tests for the `conda pypi index` subcommand.
"""

import json
import shutil
from argparse import Namespace
from pathlib import Path

import pytest

from conda_pypi.cli.index import execute, validate_dir_and_return_whl_files

here = Path(__file__).parent.parent


def test_cli(conda_cli):
    """
    Test that index subcommands exist.
    """
    out, err, rc = conda_cli("pypi", "index", "--help", raises=SystemExit)
    assert rc.value.code == 0
    assert "DIRECTORY" in out


def test_validate_dir_not_a_directory(tmp_path):
    """Test invalid dir"""
    not_a_dir = tmp_path / "file.txt"
    with pytest.raises(Exception):
        validate_dir_and_return_whl_files(not_a_dir)


def test_validate_dir_empty(tmp_path):
    """Test empty dir"""
    with pytest.raises(SystemExit):
        validate_dir_and_return_whl_files(tmp_path)


def test_validate_dir_with_empty_subdirs(tmp_path):
    """Test dir with empty subdirs"""
    (tmp_path / "somedir").mkdir()
    with pytest.raises(SystemExit):
        validate_dir_and_return_whl_files(tmp_path)


def test_validate_dir_no_subdirectories(tmp_path):
    (tmp_path / "somefile.txt").write_text("hello")
    with pytest.raises(SystemExit):
        validate_dir_and_return_whl_files(tmp_path)


def test_validate_dir_returns_wheels():
    """Test valid dir"""
    result = validate_dir_and_return_whl_files(here / "pypi_local_index")
    assert len(result) > 1
    assert any(wheel.name == "demo_package-0.1.0-py3-none-any.whl" for wheel in result)


def test_execute_no_directory():
    args = Namespace(directory=None)
    with pytest.raises(SystemExit):
        execute(args)


def test_execute_indexes_wheels(tmp_path):
    """
    execute() reads .whl files from a directory structure and produces
    a repodata.json with entries under v3.whl.
    """
    shutil.copytree(here / "pypi_local_index", tmp_path / "pypi_local_index")

    args = Namespace(directory=tmp_path / "pypi_local_index")
    result = execute(args)

    assert result == 0

    repodata = json.loads((tmp_path / "pypi_local_index" / "noarch" / "repodata.json").read_text())
    assert "v3" in repodata
    assert "whl" in repodata["v3"]
    assert len(repodata["v3"]["whl"]) == 6


def test_execute_reports_failed_wheels(tmp_path, capsys):
    """Test failed wheels reported"""
    pkg_dir = tmp_path / "bad-package"
    pkg_dir.mkdir()
    (pkg_dir / "bad_package-1.0.0-py3-none-any.whl").write_bytes(b"not a real wheel")

    args = Namespace(directory=tmp_path)
    result = execute(args)

    assert result == 0
    captured = capsys.readouterr()
    assert "failed" in captured.out
