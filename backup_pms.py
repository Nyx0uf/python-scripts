#!/usr/bin/env python3
# coding: utf-8

"""
Backup Plex Media Server library
"""

import os
from pathlib import Path
from utils import io

if __name__ == "__main__":
    HOME_PATH = Path("/home/nyxouf")
    BACKUP_PATH = Path("/home/nyxouf/tmp_pms")
    BACKUP_FILE = Path("pms.tar.lz4")

    io.rm(BACKUP_PATH)
    io.mkdir(BACKUP_PATH)
    io.cd(BACKUP_PATH)
    os.system("rsync --quiet --archive --exclude 'Logs' --exclude 'Crash Reports' --exclude 'plexmediaserver.pid' --exclude 'Updates' '/var/lib/plex' .")
    io.cd(HOME_PATH)
    TARCF = f"tar cf - {str(BACKUP_PATH)} | lz4 -1 > {str(BACKUP_FILE)}"
    os.system(TARCF)
    io.chown(BACKUP_FILE, "nyxouf", "nyxouf")
    io.chmod(BACKUP_FILE, 777)
    io.rm(BACKUP_PATH)
    io.mv(BACKUP_FILE, f"/media/nyxouf/internal/{str(BACKUP_FILE)}")
