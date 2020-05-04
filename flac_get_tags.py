#!/usr/bin/env python3
# coding: utf-8

"""
Get a unique list of all tags present in a list of flac files
[!] flac must be installed and in your $PATH
ex: flac_get_tags.py -src /path/to/files
"""

import argparse
from pathlib import Path
from queue import Queue
from shlex import quote
from typing import List
from threading import Lock
from utils import common

LOCK = Lock()

def get_tags(flac_file: str) -> List[str]:
    """return list of tags for `flac_file`"""
    metaflac = f"metaflac --export-tags-to=- {quote(flac_file)}"
    data = common.system_call(metaflac).decode('utf-8')
    lines = data.split("\n")
    return list(filter(lambda x: "=" in x, lines))

def list_tags(p_queue: Queue, all_tags: List[str]):
    """Thread"""
    while p_queue.empty() is False:
        flac_file: Path = p_queue.get()
        sflac = str(flac_file)
        tags = get_tags(sflac)
        t = list(map(lambda x: x.split("=")[0], tags))
        LOCK.acquire()
        all_tags.extend(t)
        LOCK.release()
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory or audio file")
    args = parser.parse_args()

    if common.which("metaflac") is None:
        common.abort("[!] flac not found in $PATH")

    # Sanity check
    if args.src.exists() is False:
        common.abort(parser.format_help())

    # Get files list
    files = common.walk_directory(args.src.resolve(), lambda x: x.suffix == ".flac")
    queue = common.as_queue(files)
    print(f"{common.COLOR_WHITE}[+] {len(files)} file{'s' if len(files) != 1 else ''} to consider")

    # Clean
    ALLTAGS = []
    common.parallel(list_tags, (queue, ALLTAGS))
    print(f"----\n{sorted(set(ALLTAGS))}\n----")
