#!/usr/bin/env python3
# coding: utf-8

import argparse
from datetime import datetime
from plexapi.server import PlexServer
from utils import logger


def ms_to_min(ms: int) -> int:
    return int(ms / 60000)


def format_datetime(date: datetime) -> str:
    return date.strftime("%Y-%m-%d")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("plexUrl", type=str, help="Plex url (domain.com:port)")
    parser.add_argument("token", type=str, help="Plex token")
    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="store_true", default=True, help="Verbose mode")
    args = parser.parse_args()
    LOGGER = logger.Logger(args.verbose)

    plex = PlexServer(args.plexUrl, args.token)
    movies = plex.library.section('Films')
    for video in movies.all():  # [:1]
        if "endgame" not in video.title.lower():
            continue
        nfo = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
        nfo += '<movie>\n'

        nfo += f'\t<title>{video.title}</title>\n'
        nfo += f'\t<sorttitle>{video.titleSort}</sorttitle>\n'
        nfo += f'\t<originaltitle>{video.originalTitle}</originaltitle>\n'
        nfo += f'\t<userrating>{video.userRating}</userrating>\n'
        nfo += f'\t<plot>{video.summary}</plot>\n'
        nfo += f'\t<tagline>{video.tagline}</tagline>\n'
        nfo += f'\t<runtime>{ms_to_min(video.duration)}</runtime>\n'
        nfo += f'\t<mpaa>{video.contentRating}</mpaa>\n'
        nfo += f'\t<studio>{video.studio}</studio>\n'
        nfo += f'\t<year>{video.year}</year>\n'
        premiered = format_datetime(video.originallyAvailableAt)
        nfo += f'\t<premiered>{premiered}</premiered>\n'

        for genre in video.genres:
            nfo += f'\t<genre>{genre}</genre>\n'

        for country in video.countries:
            nfo += f'\t<country>{country}</country>\n'

        for director in video.directors:
            nfo += f'\t<director>{director}</director>\n'

        for writer in video.writers:
            nfo += f'\t<credits>{writer}</credits>\n'
            nfo += f'\t<writer>{writer}</writer>\n'

        for producer in video.producers:
            nfo += f'\t<producer>{producer}</producer>\n'

        # for role in video.roles:
        #    print(f'{role.tag} -> {role.role} {role.thumb}')

        # for rating in video.ratings:
        #    print(f'{rating.type} -> {rating.value} ({rating.image})')

        for guid in video.guids:
            if "imdb" in guid.id:
                id = guid.id.replace("imdb://", "")
                nfo += f'\t<uniqueid type="imdb">{id}</uniqueid>\n'
            if "tmdb" in guid.id:
                id = guid.id.replace("tmdb://", "")
                nfo += f'\t<uniqueid type="tmdb">{id}</uniqueid>\n'
            if "tvdb" in guid.id:
                id = guid.id.replace("tvdb://", "")
                nfo += f'\t<uniqueid type="tvdb">{id}</uniqueid>\n'

        nfo += '</movie>\n'
        LOGGER.log(f"{nfo}")
