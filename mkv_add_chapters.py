#!/usr/bin/env python3
# coding: utf-8

"""
Add chapters to mkv
[!] mkvtoolnix must be installed and in your $PATH
ex: mkv_add_chapters.py --src /path/to/movies/
"""

import os
import argparse
from pathlib import Path
from shlex import quote
from typing import List
from utils import common

def merge_chapters(chaps: List[Path], vids: List[Path]):
    """Merge `chaps` into `vids`"""
    for idx, _ in enumerate(chaps):
        chap = chaps[idx]
        vid = vids[idx]
        mkvmerge = f'mkvpropedit --chapters {quote(str(chap))} {quote(str(vid))}'
        os.system(mkvmerge)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["mkvmerge"])
    if args.src.exists() is False or args.src.is_dir() is False:
        common.abort(parser.format_help())

    # list chapters
    chaps_files = common.list_directory(args.src, lambda x: x.suffix == ".xml", True)
    # list vids
    vids_files = common.list_directory(args.src, lambda x: x.suffix == ".mkv", True)

    if len(chaps_files) != len(vids_files):
        common.abort(f"[!] Error: {len(chaps_files)} chapter files and {len(vids_files)} video files")

    # Merge
    merge_chapters(chaps_files, vids_files)
