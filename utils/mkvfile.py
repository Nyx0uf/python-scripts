#!/usr/bin/env python3
# coding: utf-8

"""
MKV file helper
"""

import json
from pathlib import Path
from typing import List, Dict
from shlex import quote
from utils import common

# Video codecs
CODEC_VIDEO_MPEG2 = str("mpeg-1/2")
CODEC_VIDEO_MPEG4 = str("mpeg-4p2")
CODEC_VIDEO_H264 = str("mpeg-4p10/avc/h.264")
CODEC_VIDEO_H264_2 = str("avc/h.264/mpeg-4p10")
CODEC_VIDEO_H265 = str("mpeg-h/hevc/h.265")
CODEC_VIDEO_H265_2 = str("hevc/h.265/mpeg-h")
CODEC_VIDEO_VC1 = str("vc-1")
CODEC_VIDEO_AV1 = str("av1")
# Audio codecs
CODEC_AUDIO_AAC = str("aac")
CODEC_AUDIO_AC3 = str("ac-3")
CODEC_AUDIO_AC3_2 = str("ac-3 dolby surround ex")
CODEC_AUDIO_ALAC = str("alac")
CODEC_AUDIO_DTS = str("dts")
CODEC_AUDIO_DTSES = str("dts-es")
CODEC_AUDIO_DTSHDMA = str("dts-hd master audio")
CODEC_AUDIO_DTSHRA = str("dts-hd high resolution audio")
CODEC_AUDIO_EAC3 = str("e-ac-3")
CODEC_AUDIO_FLAC = str("flac")
CODEC_AUDIO_MP2 = str("mp2")
CODEC_AUDIO_MP3 = str("mp3")
CODEC_AUDIO_OPUS = str("opus")
CODEC_AUDIO_PCM = str("a_ms/acm")
CODEC_AUDIO_TRUEHD = str("truehd")
CODEC_AUDIO_TRUEHDATMOS = str("truehd atmos")
CODEC_AUDIO_VORBIS = str("vorbis")
CODEC_AUDIO_WAVPACK4 = str("wavpack4")
# Subtitles codecs
CODEC_SUBTITLE_ASS = str("substationalpha")
CODEC_SUBTITLE_MKS = str("substationalpha")
CODEC_SUBTITLE_PGS = str("hdmv pgs")
CODEC_SUBTITLE_SRT = str("subrip/srt")
CODEC_SUBTITLE_VOBSUB = str("vobsub")
SUBTITLE_TYPE_ASS = str("ass")
SUBTITLE_TYPE_MKS = str("mks")
SUBTITLE_TYPE_PGS = str("pgs")
SUBTITLE_TYPE_SRT = str("srt")
SUBTITLE_TYPE_VOBSUB = str("vobsub")

CODEC_EXTENSION_MAP: Dict[str, str] = {
    # video
    CODEC_VIDEO_MPEG2: str('.mpeg2'),
    CODEC_VIDEO_MPEG4: str('.mpeg4'),
    CODEC_VIDEO_H264: str('.264'),
    CODEC_VIDEO_H264_2: str('.264'),
    CODEC_VIDEO_H265: str('.265'),
    CODEC_VIDEO_H265_2: str('.265'),
    CODEC_VIDEO_VC1: str('.vc1'),
    CODEC_VIDEO_AV1: str('.av1'),
    # audio
    CODEC_AUDIO_AAC: str(".aac"),
    CODEC_AUDIO_AC3: str(".ac3"),
    CODEC_AUDIO_AC3_2: str(".ac3"),
    CODEC_AUDIO_ALAC: str(".m4a"),
    CODEC_AUDIO_DTS: str(".dts"),
    CODEC_AUDIO_DTSES: str(".es.dts"),
    CODEC_AUDIO_DTSHDMA: str(".hdma.dts"),
    CODEC_AUDIO_DTSHRA: str(".hra.dts"),
    CODEC_AUDIO_EAC3: str(".eac3"),
    CODEC_AUDIO_FLAC: str(".flac"),
    CODEC_AUDIO_MP2: str(".mp2"),
    CODEC_AUDIO_MP3: str(".mp3"),
    CODEC_AUDIO_OPUS: str(".opus"),
    CODEC_AUDIO_PCM: str(".wav"),
    CODEC_AUDIO_TRUEHD: str(".thd"),
    CODEC_AUDIO_TRUEHDATMOS: str(".thd"),
    CODEC_AUDIO_VORBIS: str(".ogg"),
    CODEC_AUDIO_WAVPACK4: str(".wav"),
    # subtitles
    CODEC_SUBTITLE_ASS: str('.ass'),
    CODEC_SUBTITLE_MKS: str('.mks'),
    CODEC_SUBTITLE_PGS: str('.sup'),
    CODEC_SUBTITLE_SRT: str('.srt'),
    CODEC_SUBTITLE_VOBSUB: str('.vobsub')
}

CODEC_AUDIO_SCORE: Dict[str, int] = {
    CODEC_AUDIO_AAC: 5,
    CODEC_AUDIO_AC3: 6,
    CODEC_AUDIO_AC3_2: 6,
    CODEC_AUDIO_ALAC: 11,
    CODEC_AUDIO_DTS: 9,
    CODEC_AUDIO_DTSES: 10,
    CODEC_AUDIO_DTSHDMA: 14,
    CODEC_AUDIO_DTSHRA: 13,
    CODEC_AUDIO_EAC3: 7,
    CODEC_AUDIO_FLAC: 12,
    CODEC_AUDIO_MP2: 1,
    CODEC_AUDIO_MP3: 2,
    CODEC_AUDIO_OPUS: 4,
    CODEC_AUDIO_PCM: 8,
    CODEC_AUDIO_TRUEHD: 15,
    CODEC_AUDIO_TRUEHDATMOS: 16,
    CODEC_AUDIO_VORBIS: 3,
    CODEC_AUDIO_WAVPACK4: 3,
}

CODEC_SUBTITLE_TYPE_MAP: Dict[str, str] = {
    SUBTITLE_TYPE_ASS: CODEC_SUBTITLE_ASS,
    SUBTITLE_TYPE_MKS: CODEC_SUBTITLE_MKS,
    SUBTITLE_TYPE_PGS: CODEC_SUBTITLE_PGS,
    SUBTITLE_TYPE_SRT: CODEC_SUBTITLE_SRT,
    SUBTITLE_TYPE_VOBSUB: CODEC_SUBTITLE_VOBSUB
}


class MkvTrack:
    """Represents a track within a mkv file"""

    def __init__(self, json_data):
        self.id = int(json_data["id"])
        self.type = str(json_data["type"].lower())
        self.codec = str(json_data["codec"].lower())
        self.file_extension = str(CODEC_EXTENSION_MAP[self.codec])
        self.audio_bits = None
        properties = json_data["properties"]
        if properties is not None:
            self.uid = int(properties["uid"])
            self.name = str(properties["track_name"]
                            ) if "track_name" in properties else ""
            self.forced = bool(properties["forced_track"])
            if self.forced is False and "forced" in self.name.lower():
                self.forced = bool(True)
            self.default = bool(properties["default_track"])
            language = properties["language"]
            if language is not None:
                self.lang = str(language.lower())
            if "audio_channels" in properties:
                self.audio_channels = int(properties["audio_channels"])
            if "audio_bits_per_sample" in properties:
                self.audio_bits = int(properties["audio_bits_per_sample"])

    def __str__(self):
        return "{}:{}|{}".format(self.id, self.name, self.lang)

    def __repr__(self):
        return "{}:{}|{}".format(self.id, self.name, self.lang)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def is_commentary(self) -> bool:
        """check if the track is marked as commentary"""
        return "commentary" in self.name.lower()

    def audio_score(self) -> int:
        """Compute an audio score based on the number of channels and codec"""
        score = self.audio_channels
        score += CODEC_AUDIO_SCORE[self.codec]
        return score


class MkvAttachment:
    """Represents an attachment within a mkv file"""

    def __init__(self, json_data: str):
        self.id = int(json_data["id"])
        self.uid = int(json_data["properties"]["uid"])
        self.file_name = str(json_data["file_name"])
        self.content_type = str(json_data["content_type"])

    def __str__(self):
        return "{}:{}".format(self.id, self.file_name)

    def __repr__(self):
        return "{}:{}".format(self.id, self.file_name)

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other):
        return self.id == other.id and self.uid == other.uid


class MkvFile:
    """Represents a mkv file"""

    def __init__(self, path: Path):
        self.is_valid = False
        self.chaptered = False
        self.tracks: List[MkvTrack] = []
        self.attachments: List[MkvAttachment] = []
        if path.exists() is True:
            self.path = path
            self.is_valid = True
            infos = MkvFile.get_file_infos(path)
            self.chaptered = bool(
                infos["chapters"] is not None and infos["chapters"])
            self.file_name = str(infos["file_name"])

            # Tracks
            for t in infos["tracks"]:
                self.tracks.append(MkvTrack(t))

            # Attachments
            if infos["attachments"]:
                for a in infos["attachments"]:
                    self.attachments.append(MkvAttachment(a))

    def __str__(self):
        return str(self.path) if self.path is not None else ""

    def __repr__(self):
        return str(self.path) if self.path is not None else ""

    def __hash__(self):
        return hash(str(self.path))

    def __eq__(self, other):
        return self.path == other.path

    def video_codec_desc(self) -> str:
        """return smth like AVC High10@L4.1 24fps"""
        return common.system_call(f'mediainfo --Inform="Video;%Format% %Format_Profile% %FrameRate%fps" {quote(str(self.path))}').decode("utf-8").strip()

    @staticmethod
    def get_file_infos(path: Path):
        """Invoke mkvmerge to get infos"""
        a = common.system_call(f'mkvmerge -J {quote(str(path))}')
        return json.loads(a)
