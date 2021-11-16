#!/usr/bin/env python3
# coding: utf-8

"""
A/V Types
"""

from typing import List
from pathlib import Path
from shlex import quote
from utils import common

AUDIO_EXTENSIONS: List[str] = [
    str('.aac'),
    str('.ac3'),
    str('.aif'),
    str('.aiff'),
    str('.dts'),
    str('.eac3'),
    str('.flac'),
    str('.m4a'),
    str('.mka'),
    str('.mp3'),
    str('.oga'),
    str('.ogg'),
    str('.opus'),
    str('.thd'),
    str('.wav'),
    str('webm'),
    str('.wma'),
]

VIDEO_EXTENSIONS: List[str] = [
    str('.264'),
    str('.265'),
    str('.avi'),
    str('.mkv'),
    str('.mov'),
    str('.mp4'),
    str('.mpg'),
    str('.mpeg'),
    str('.mpeg2'),
    str('.vc1'),
    str('.wmv'),
]

SUBTITLE_EXTENSIONS: List[str] = [
    str('.ass'),
    str('.pgs'),
    str('.srt'),
    str('.ssa'),
    str('.txt'),
]


def get_file_infos(filepath: Path) -> str:
    """ffmpeg -i `filepath`"""
    data = common.system_call(
        f"ffmpeg -hide_banner -i {quote(str(filepath))}", True).decode("utf-8")
    return data
