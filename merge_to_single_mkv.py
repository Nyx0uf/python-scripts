#!/usr/bin/env python3
# coding: utf-8

import argparse
import subprocess
import os
from shlex import quote
from pathlib import Path
from typing import List
from utils import common


def make_chapters_metadata(files: List[Path], input_dir: Path):
    """Create chapters file in ffmpeg metadata format"""
    chapters = {}
    chap_number = 1
    for vid_file in files:
        command = f"ffprobe -v quiet -of csv=p=0 -show_entries format=duration {quote(str(vid_file))}"
        duration_in_microseconds = int((subprocess.run(command, shell=True, capture_output=True, check=False).stdout.decode().strip().replace(".", "")))
        if 100 <= chap_number < 1000:
            number = f"0{chap_number}"
        elif 10 <= chap_number < 100:
            number = f"00{chap_number}"
        else:
            number = f"000{chap_number}"
        chapters[number] = {"duration": duration_in_microseconds}
        chap_number += 1

    chapters["0001"]["start"] = 0
    for n in range(1, len(chapters)):
        chapter = f"{n:04d}"
        next_chapter = f"{n + 1:04d}"
        chapters[chapter]["end"] = chapters[chapter]["start"] + chapters[chapter]["duration"]
        chapters[next_chapter]["start"] = chapters[chapter]["end"] + 1
    last_chapter = f"{len(chapters):04d}"
    chapters[last_chapter]["end"] = chapters[last_chapter]["start"] + chapters[last_chapter]["duration"]

    metadatafile = f"{quote(str(input_dir))}/ffmpeg_metadata.txt"
    with open(metadatafile, "w+", encoding="utf-8") as m:
        m.writelines(";FFMETADATA1\n")
        for chapter in chapters:
            ch_meta = """
[CHAPTER]
TIMEBASE=1/1000000
START={}
END={}
title={}
""".format(chapters[chapter]["start"], chapters[chapter]["end"], chapter)
            m.writelines(ch_meta)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory")
    args = parser.parse_args()

    # list vids
    video_files = common.list_directory(args.input, lambda x: x.suffix in (".mkv", ".mp4"), True)

    # Make the list of videos in ffmpeg format
    vlname = Path(args.input / "videos_list.txt")
    if vlname.exists():
        vlname.unlink()
    for filename in video_files:
        with open(vlname, mode="a", encoding="utf-8") as f:
            f.write(f"file '{filename}'\n")

    make_chapters_metadata(video_files, args.input)
    ffmpeg = f"ffmpeg -y -f concat -i {quote(str(vlname))} -i {quote(str(args.input / 'ffmpeg_metadata.txt'))} -map_metadata 1 -c copy a.mkv"
    os.system(ffmpeg)
