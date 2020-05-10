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
    parser.add_argument("input", type=Path, help="Path to directory or single file (all files must be .mkv)")
    parser.add_argument("-type", dest="type", type=str, default="image", help="Type of attachments to remove (comma separated list, between font and image)")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["mkvmerge"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.input.resolve(), lambda x: x.suffix == ".mkv", True)

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
