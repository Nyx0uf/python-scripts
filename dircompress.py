#!/usr/bin/env python3
# coding: utf-8

import argparse
import os
from pathlib import Path
from shlex import quote
from utils import common, io

BIN7Z = "7zz"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory")
    args = parser.parse_args()

    io.cd(args.input)

    # Get files list
    all_directories = common.list_directory(Path("."))

    for a_dir in all_directories:
        # 7z a -t7z -m0=lzma2 -mx=9 -mfb=64 -md=32m -ms=on "asstraffic.7z" AssTraffic
        filename = quote(str(a_dir))
        print(f"file = {filename}")
        os.system(f"{BIN7Z} a -t7z -m0=lzma2 -mx=9 -mfb=64 -md=32m -ms=on {filename}.7z {filename}")
