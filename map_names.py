#!/usr/bin/env python3
# coding: utf-8

"""
map names of files from one folder to another
ex: map_names.py -src src -dst dst
"""

import shutil
import argparse
from pathlib import Path
from typing import List
from utils import common

def map_names(src: List[Path], dst: List[Path], real=False):
    """rename `dst` to match `src`"""
    for idx, val in enumerate(src):
        src_filename = val.name
        target_file = dst[idx]
        new_file = target_file.with_name(src_filename)
        if real is False:
            print(f"{common.COLOR_WHITE}{target_file}\n ↳ {common.COLOR_YELLOW}{new_file}{common.COLOR_WHITE}")
        else:
            shutil.move(target_file, new_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, help="Path to directory or file")
    parser.add_argument("-dst", action="store", dest="dst", type=Path, help="Path to directory or file")
    args = parser.parse_args()

    # Sanity check
    if args.src is None or args.dst is None:
        common.abort(parser.format_help())

    # If path is a directory, get a list of files
    src_path = args.src.resolve()
    src_files = common.list_directory(src_path, sort=True)
    dst_path = args.dst.resolve()
    dst_files = common.list_directory(dst_path, sort=True)
    if len(src_files) != len(dst_files):
        common.abort(f"[!] Number of files mismatch: src={len(src_files)} dst={len(dst_files)}")

    map_names(src_files, dst_files, False)
    ok = input("Proceed (y/n) ? ")
    if common.str2bool(str(ok)) is True:
        map_names(src_files, dst_files, True)