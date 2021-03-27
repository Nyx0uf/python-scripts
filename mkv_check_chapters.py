#!/usr/bin/env python3
# coding: utf-8

"""
"""

import argparse
from queue import Queue
from pathlib import Path
from utils import common
from utils import mkvfile

def check_chaptered(p_queue: Queue):
    """PNG export thread"""
    while p_queue.empty() is False:
        original_file: Path = p_queue.get()
        try:
            mkv = mkvfile.MkvFile(original_file)
            if mkv.chaptered is False:
                print(f"{original_file}")
        except:
            print(f"ERROR PARSING :::: {original_file}")
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single MKV file")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["mkvmerge"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    files = common.list_directory(args.input.resolve(), lambda x: x.suffix == ".mkv", True)
    queue = common.as_queue(files)

    common.parallel(check_chaptered, (queue,))
