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
from typing import List
from utils import common
from utils import mkvfile


def extract_attachment(path: Path, p_attachment: mkvfile.MkvAttachment):
    """Extractor function"""
    cmd = f"mkvextract attachments {quote(str(path))} {p_attachment.id}:{quote(p_attachment.file_name.lower())}"
    os.system(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single MKV file")
    parser.add_argument("-t", "--type", dest="type", type=str, default="font,image", help="Type of attachments to extract (comma separated list, between font and image)")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["mkvmerge", "mkvextract"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.input.resolve(), lambda x: x.suffix == ".mkv", True)

    # Extract all attachments
    extracted: List[str] = []
    for f in files:
        mkv = mkvfile.MkvFile(f)
        if mkv.is_valid is False:
            continue

        for attachment in mkv.attachments:
            if attachment.file_name.lower() in extracted:
                continue
            extract_attachment(f, attachment)
            extracted.append(attachment.file_name.lower())
