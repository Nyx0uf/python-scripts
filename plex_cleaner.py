#!/usr/bin/env python3
# coding: utf-8

"""
Remove files from plex library after 30 days
"""

import time
import argparse
from pathlib import Path
from typing import List
from utils import common

MOVIES_TO_REMOVE: List[Path] = [
    Path("Ibiza (2019).mkv"),
]
TIME_TO_KEEP = float(31 * 86400)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to movies directory")
    args = parser.parse_args()

    # Sanity checks
    if args.src.exists() is False:
        common.abort(parser.format_help())

    # Get a list of files
    path = args.src.resolve()
    target = [path / x for x in MOVIES_TO_REMOVE]
    files = common.list_directory(path, lambda x: x in target)

    now = time.time()
    for f in files:
        creation_time = f.stat().st_ctime
        limit = creation_time + TIME_TO_KEEP
        if limit < now:
            print(f"[+] Removing <{f}>")
            f.unlink()
        else:
            exp = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime(limit))
            print(f"[+] Keeping <{f}> (until {exp})")
