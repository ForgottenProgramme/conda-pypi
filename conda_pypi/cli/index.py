from argparse import Namespace, _SubParsersAction
from pathlib import Path

from conda.auxlib.ish import dals
from conda.exceptions import ArgumentError

from conda_pypi.conda_build_utils import sha256_checksum
from conda_pypi.index import store_pypi_metadata, update_index
from conda_pypi.license_files import package_metadata_from_metadata_body


def configure_parser(parser: _SubParsersAction) -> None:
    """Configure all subcommand arguments and options via argparse"""

    summary = "Index a directory of `.whl` files to generate repodata.json"
    description = summary
    epilog = dals("""
    Generate a `repodata.json` file from a directory of `.whl` files.
    This is useful for creating a local conda channel from a collection of wheel files.
    Examples:
    `conda pypi index <directory>`
    """)
    index = parser.add_parser(
        "index",
        help=summary,
        description=description,
        epilog=epilog,
    )
    index.add_argument(
        "directory",
        metavar="DIRECTORY",
        type=Path,
        help="Directory containing .whl files to index",
    )


def execute(args: Namespace) -> int:
    """Entry point for the `conda pypi index` subcommand"""

    directory = args.directory

    # ensure directory is provided
    if not directory:
        raise SystemExit(
            "No directory provided. Please specify a directory containing wheels to index."
        )

    # ensure provided path is a directory and follows expected structure
    # Expected structure:
    # root/
    #   <package>/ <package>-*.whl

    if not directory.is_dir():
        raise ArgumentError(f"Not a directory: {directory}")

    entries = list(directory.iterdir())
    if not entries:
        raise SystemExit(f"No wheel subdirectories found in the given directory: {directory}")

    # notify user of ignored invalid entries
    invalid_entries = [entry for entry in entries if not entry.is_dir()]
    if invalid_entries:
        print(
            f"Found invalid entries (not wheel directories) in the given directory, ignoring them: {invalid_entries}"
        )

    # find valid entries
    valid_entries = [entry for entry in entries if entry.is_dir()]
    if not valid_entries:
        raise SystemExit(
            f"No valid wheel subdirectories found in the given directory: {directory}"
        )

    all_wheels = []
    for entry in valid_entries:
        # one wheel file per subdirectory is expected
        all_wheels.extend(entry.glob("*.whl"))

    if not all_wheels:
        raise SystemExit(f"No wheel files found in the given directory: {directory}")

    for wheel in all_wheels:
        wheel_metadata = package_metadata_from_metadata_body(wheel.read_dist_info("METADATA"))

        # convert the output to json format using the `json` property of the PackageMetadata class
        wheel_metadata_json = wheel_metadata.json

        # generate the expected dict structure of pypi metadata with the relevant fields as needed by the `pypi_to_repodata` function.
        pypi_data = {
            "info": {
                "name": wheel_metadata_json.get("name"),
                "version": wheel_metadata_json.get("version"),
                "requires_dist": wheel_metadata_json.get("requires_dist", []),
                "requires_python": wheel_metadata_json.get("requires_python"),
            },
            "urls": [
                {
                    "packagetype": "bdist_wheel",
                    "filename": wheel.name,
                    "url": str(wheel),
                    "size": wheel.stat().st_size,
                    "digests": {"sha256": sha256_checksum(str(wheel))},
                }
            ],
        }

        # store the converted metadata in the conda index cache
        store_pypi_metadata(pypi_data)

    # create a noarch subdir as expected by conda index
    noarch_dir = directory / "noarch"
    noarch_dir.mkdir(parents=True, exist_ok=True)

    update_index(directory)
