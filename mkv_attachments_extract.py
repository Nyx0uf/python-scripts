#!/usr/bin/env python3
# coding: utf-8

"""
Extract all fonts in a given .mkv file or directory of .mkv files
[!] mkvtoolnix must be installed and in your $PATH
ex: mkv_attachments_extract.py -src /path/to/file.mkv
"""

import os
import argparse
from pathlib import Path
from shlex import quote
from utils import common
from utils import mkvfile

def extract_attachment(path: Path, attachment: mkvfile.MkvAttachment):
    """Extractor function"""
    cmd = f"mkvextract attachments {quote(str(path))} {attachment.id}:{quote(attachment.file_name)}"
    os.system(cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory or single file (all files must be .mkv)")
    parser.add_argument("-type", action="store", dest="type", type=str, default="font,image", help="Type of attachments to extract (comma separated list, between font and image)")
    args = parser.parse_args()

    # Sanity checks
    if common.which("mkvmerge") is None or common.which("mkvextract") is None:
        common.abort("[!] mkvtoolnix not found in $PATH")

    if args.src.exists() is False:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.src.resolve(), lambda x: x.suffix == ".mkv", True)

    # Extract all attachments
    for f in files:
        mkv = mkvfile.MkvFile(f)
        if mkv.is_valid is False:
            continue

        for attachment in mkv.attachments:
            extract_attachment(f, attachment)
