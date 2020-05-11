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

def merge_chapters(chaps: List[Path], vids: List[Path], delete: bool):
    """Merge `chaps` into `vids`"""
    for idx, _ in enumerate(chaps):
        chap = chaps[idx]
        vid = vids[idx]
        mkvmerge = f'mkvpropedit --chapters {quote(str(chap))} {quote(str(vid))}'
        os.system(mkvmerge)
        if delete is True:
            chap.unlink()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory")
    parser.add_argument("-d", "--delete", dest="delete", action="store_true", help="Delete chapters file after merge")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["mkvmerge"])
    if args.input.exists() is False or args.input.is_dir() is False:
        common.abort(parser.format_help())

    # list chapters
    chaps_files = common.list_directory(args.input, lambda x: x.suffix == ".xml" or x.suffix == ".txt", True)
    # list vids
    video_files = common.list_directory(args.input, lambda x: x.suffix == ".mkv", True)

    if len(chaps_files) != len(video_files):
        common.abort(f"{common.COLOR_RED}[!] ERROR: Number of files mismatch, chapters={len(chaps_files)} video={len(video_files)}{common.COLOR_WHITE}")

    # Merge
    merge_chapters(chaps_files, video_files, args.delete)
