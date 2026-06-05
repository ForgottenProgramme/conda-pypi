import sys
from pathlib import Path

HERE = Path(__file__).parent

PYPI_LOCAL_INDEX = HERE / "pypi_local_index"
CONDA_LOCAL_CHANNEL = HERE / "conda_local_channel"

# Use the same Python version as the test environment
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"
