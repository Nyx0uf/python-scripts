#!/usr/bin/env python3
# coding: utf-8

"""
take multiple screenshots with mpv
"""

import os
import argparse
from pathlib import Path
from shlex import quote
from utils import common

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to movie file")
    parser.add_argument("-n", "--number-of-screenshots", dest="number_of_screenshots", type=int, default=10, help="Number of screenshots to take")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["ffprobe", "mpv"])
    if args.input.exists() is False or args.input.is_file() is False:
        common.abort(parser.format_help())

    duration = float(common.system_call(f'ffprobe -i {quote(str(args.input))} -show_entries format=duration -v quiet -of csv="p=0"').decode("utf-8").split('.')[0])

    step = int(duration / args.number_of_screenshots + 1)
    current = step
    for i in range(args.number_of_screenshots):
        scname = f'{args.input.stem}-{i:0>2}-{current}.png'
        cmd = f'mpv {quote(str(args.input))} --no-config --quiet --no-terminal --aid=no --sid=no --frames=1 --start={current} --o={quote(scname)}'
        os.system(cmd)
        current += step
