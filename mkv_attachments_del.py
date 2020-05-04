#!/usr/bin/env python3
# coding: utf-8

"""
Clear attachments from mkv files
[!] mkvtoolnix must be installed and in your $PATH
"""

import os
import argparse
from pathlib import Path
from shlex import quote
from typing import List
from utils import common
from utils import mkvfile

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, help="Path to directory or single file (all files must be .mkv)")
    parser.add_argument("-type", action="store", dest="type", type=str, default="image", help="Type of attachments to remove (comma separated list, between font and image)")
    args = parser.parse_args()

    # Sanity checks
    if common.which("mkvmerge") is None:
        common.abort("[!] mkvtoolnix not found in $PATH")

    if args.src is None or args.type is None:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.src.resolve(), lambda x: x.suffix == ".mkv", True)

    types: List[str] = []
    if "image" in args.type:
        types.extend(["image/jpeg", "image/png"])
    if "font" in args.type:
        types.extend(["application/x-truetype-font", "application/vnd.ms-opentype", "application/font-sfnt"])

    # Extract all attachments
    for f in files:
        mkv = mkvfile.MkvFile(f)
        if mkv.is_valid is False:
            continue

        # Strip images
        toremove: List[mkvfile.MkvAttachment] = list(filter(lambda x: x.content_type in types, mkv.attachments))
        for attachment in toremove:
            os.system(f"mkvpropedit {quote(str(f))} --delete-attachment mime-type:{attachment.content_type}")
