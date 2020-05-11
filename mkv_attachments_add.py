#!/usr/bin/env python3
# coding: utf-8

"""
Add attachments to mkv files
[!] mkvtoolnix must be installed and in your $PATH
"""

import os
import argparse
from pathlib import Path
from shlex import quote
from utils import common

def add_attachment(mkv: Path, attachment: Path):
    """Add `attachment` to `mkv`"""
    mime = None
    la = attachment.name.lower()
    if "ttf" in la:
        mime = 'application/x-truetype-font'
    elif "otf" in la:
        mime = 'application/vnd.ms-opentype'
    elif "jpeg" in la or "jpg" in la:
        mime = 'image/jpeg'

    if mime is not None:
        cmd = f'mkvpropedit {quote(str(mkv))} --attachment-mime-type {mime} --add-attachment {quote(str(attachment))}'
    else:
        cmd = f'mkvpropedit {quote(str(mkv))} --add-attachment {quote(str(attachment))}'
    os.system(cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("attachments_path", type=Path, help="Path to directory of attachments or single file")
    parser.add_argument("videos_path", type=Path, help="Path to directory or single video file (all files must be .mkv)")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["mkvmerge", "mkvpropedit"])
    if args.videos_path.exists() is False or args.attachments_path.exists() is False:
        common.abort(parser.format_help())

    # Get a list of files
    video_files = common.list_directory(args.videos_path.resolve(), lambda x: x.suffix == ".mkv", True)
    attachments = common.list_directory(args.attachments_path.resolve())

    # Add all attachments
    for video in video_files:
        for attachment in attachments:
            add_attachment(video, attachment)
