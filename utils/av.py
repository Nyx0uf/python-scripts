#!/usr/bin/env python3
# coding: utf-8

"""
A/V Types
"""

from typing import List

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
    str('.wma'),
]

VIDEO_EXTENSIONS: List[str] = [
    str('.264'),
    str('.265'),
    str('.avi'),
    str('.mkv'),
    str('.mp4'),
    str('.mpg'),
    str('.mpeg'),
    str('.wmv'),
]

SUBTITLE_EXTENSIONS: List[str] = [
    str('.ass'),
    str('.pgs'),
    str('.srt'),
    str('.ssa'),
    str('.txt'),
]
