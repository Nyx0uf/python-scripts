#!/usr/bin/env python3
# coding: utf-8

"""
Fix attachments mime types in mkv files
[!] mkvtoolnix must be installed and in your $PATH
"""

import os
import argparse
from pathlib import Path
from shlex import quote
from utils import common
from utils import mkvfile


def fix_attachment(p_mkv: Path, p_attachment: mkvfile.MkvAttachment):
    """Fix mime types"""
    mime = None
    if "ttf" in p_attachment.file_name.lower():
        mime = 'application/x-truetype-font'
    elif "otf" in p_attachment.file_name.lower():
        mime = 'application/vnd.ms-opentype'

    if mime is not None:
        cmd = f'mkvpropedit {quote(str(p_mkv))} --attachment-mime-type {mime} --update-attachment {p_attachment.id}'
        os.system(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single MKV file")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["mkvmerge", "mkvpropedit"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.input.resolve(), lambda x: x.suffix == ".mkv", True)

    for f in files:
        mkv = mkvfile.MkvFile(f)
        if mkv.is_valid is False:
            continue

        for attachment in mkv.attachments:
            fix_attachment(f, attachment)
