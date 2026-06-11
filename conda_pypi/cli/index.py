from argparse import _SubParsersAction, Namespace
from conda.auxlib.ish import dals
from conda.exceptions import ArgumentError
from pathlib import Path

def configure_parser(parser: _SubParsersAction) -> None:
    """Configure all subcommand arguments and options via argparse"""

    summary= "Index a directory of `.whl` files to generate repodata.json"
    description=summary
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
    index.add_argument("directory", metavar="DIRECTORY", type=Path, help="Directory containing .whl files to index")

def execute(args: Namespace) -> int:
    """Entry point for the `conda pypi index` subcommand"""

    # validate provided directory
    directory=args.directory
    if not directory.is_dir():
        raise ArgumentError(f"Expected a directory: {directory}")
    

    
    
