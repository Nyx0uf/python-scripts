#!/usr/bin/env python3
# coding: utf-8

"""
Remove files from plex library after 30 days
"""

import time
import argparse
from pathlib import Path
from utils import common, logger

LOGGER: logger.Logger

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to movies directory")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")
    parser.add_argument("-t", "--time", dest="time", type=float, default=2678400, help="Time to keep in seconds (default = 1 month)")
    args = parser.parse_args()
    LOGGER = logger.Logger(args.verbose)

    # Sanity checks
    if args.input.exists() is False or args.input.is_dir() is False:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.input.resolve())

    now = time.time()
    for f in files:
        creation_time = f.stat().st_ctime
        limit = creation_time + args.time
        if limit < now:
            LOGGER.log(f"{common.COLOR_WHITE}[+] Removing {common.COLOR_YELLOW}{f}{common.COLOR_WHITE}")
            f.unlink()
        else:
            exp = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime(limit))
            LOGGER.log(f"{common.COLOR_WHITE}[+] Keeping {common.COLOR_YELLOW}{f}{common.COLOR_WHITE} until {common.COLOR_YELLOW}{exp}{common.COLOR_WHITE}")
