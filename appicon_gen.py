#!/usr/bin/env python3
# coding: utf-8

"""
Generate all App Icon size for iOS
"""

import argparse
import os
from typing import List
from pathlib import Path
from shlex import quote
from utils import common

PIXEL_SIZES: List[str] = [
    str('16x16'),
    str('20x20'),
    str('29x29'),
    str('32x32'),
    str('40x40'),
    str('44x44'),
    str('48x48'),
    str('50x50'),
    str('55x55'),
    str('57x57'),
    str('58x58'),
    str('60x60'),
    str('64x64'),
    str('66x66'),
    str('72x72'),
    str('76x76'),
    str('80x80'),
    str('87x87'),
    str('88x88'),
    str('92x92'),
    str('96x96'),
    str('100x100'),
    str('102x102'),
    str('108x108'),
    str('114x114'),
    str('120x120'),
    str('128x128'),
    str('136x136'),
    str('144x144'),
    str('152x152'),
    str('167x167'),
    str('172x172'),
    str('180x180'),
    str('192x192'),
    str('196x196'),
    str('216x216'),
    str('234x234'),
    str('256x256'),
    str('258x258'),
    str('288x288'),
    str('384x384'),
    str('512x512'),
    str('1024x1024'),
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Image file")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["convert"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    for size in PIXEL_SIZES:
        # convert "$1" -quality 100 "${f2}.jpg"
        cmd = f"convert -quality 100 {quote(str(args.input))} -resize {size} {size}.png"
        os.system(cmd)
