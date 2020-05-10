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
    parser.add_argument("input", type=Path, help="Path to directory or single file")
    args = parser.parse_args()

    # Sanity check
    if args.input is None:
        common.abort(parser.format_help())

    # If path is a directory, get a list of files
    files = common.list_directory(args.input.resolve(), None, True)

    for f in files:
        a = str(f).encode('utf-8', "ignore")
        os.rename(str(f), a)
