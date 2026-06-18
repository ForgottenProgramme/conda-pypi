import pytest
from conda_pypi.cli.index import execute as index_execute
from conda_pypi.cli.index import validate_dir_and_return_whl_files, pypi_data_dict


def test_validate_dir_and_return_whl_files_fails():
    ...