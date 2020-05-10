#!/usr/bin/env python3
# coding: utf-8

"""
Rename several files at once following a pattern
ex: batch_name -src FLCL -bp 'FLCL - s01e' -ap ' - ' -z 1
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import List
from utils import common

def rename(src: List[Path], pattern: str, zero: str, after: str, real=False):
    """Rename `src` following `pattern`"""
    count = len(src)
    for idx, val in enumerate(src):
        good_index = idx + 1
        filepath, _ = os.path.splitext(val)
        filename = os.path.basename(filepath)
        target_filename = ""
        if zero is True:
            if count >= 100 and count < 1000:
                if good_index >= 100:
                    target_filename = f"{pattern}{good_index}"
                elif good_index < 100 and good_index >= 10:
                    target_filename = f"{pattern}0{good_index}"
                else:
                    target_filename = f"{pattern}00{good_index}"
            elif count >= 10 and count < 100:
                if good_index < 10:
                    target_filename = f"{pattern}0{good_index}"
                elif good_index >= 10:
                    target_filename = f"{pattern}{good_index}"
            else:
                target_filename = f"{pattern}{good_index}"
        if after is not None:
            target_filename += after
        target_filename += val.suffix
        new_file = filepath.replace(filename, target_filename)
        print(f"{common.COLOR_WHITE}{val}\n ↳ {common.COLOR_YELLOW}{new_file}{common.COLOR_WHITE}")
        if real is True:
            shutil.move(val, new_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory")
    parser.add_argument("-b", "--before-pattern", dest="before_pattern", type=str, help="Before pattern")
    parser.add_argument("-a", "--after-pattern", dest="after_pattern", type=str, help="After pattern")
    parser.add_argument("-z", "--zero", dest="zero", action="store_true", help="Numerote with zeros first")
    args = parser.parse_args()

    # Sanity check
    if args.input.exists() is False:
        common.abort(parser.format_help())

    # If path is a directory, get a list of files
    src_files = common.list_directory(args.input.resolve(), None, True)

    rename(src_files, args.before_pattern if args.before_pattern is not None else "", args.zero, args.after_pattern, False)
    ok = input("Proceed (y/n) ? ")
    if common.str2bool(ok) is True:
        rename(src_files, args.before_pattern if args.before_pattern is not None else "", args.zero, args.after_pattern, True)
