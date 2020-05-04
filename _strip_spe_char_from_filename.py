#!/usr/bin/env python3
# coding: utf-8

"""
Replace invalid characters from a filename
"""

import os
import argparse
from pathlib import Path
from utils import common

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, help="Path to directory")
    args = parser.parse_args()

    # Sanity check
    if args.src is None:
        common.abort(parser.format_help())

    # If path is a directory, get a list of files
    my_src_path = args.src.resolve()
    my_src_files = common.list_directory(my_src_path, None, True)

    for f in my_src_files:
        a = str(f).encode('utf-8', "ignore")
        os.rename(str(f), a)
