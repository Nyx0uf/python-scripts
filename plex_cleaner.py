#!/usr/bin/env python3
# coding: utf-8

"""
Remove files from plex library after 30 days
"""

import time
import argparse
from pathlib import Path
from utils import common

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to movies directory")
    parser.add_argument("-t", "--time", dest="time", type=float, default=2678400, help="Time to keep in seconds (default = 1 month)")
    args = parser.parse_args()

    # Sanity checks
    if args.input.exists() is False:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.input.resolve())

    now = time.time()
    for f in files:
        creation_time = f.stat().st_ctime
        limit = creation_time + args.time
        if limit < now:
            print(f"[+] Removing <{f}>")
            f.unlink()
        else:
            exp = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime(limit))
            print(f"[+] Keeping <{f}> (until {exp})")
