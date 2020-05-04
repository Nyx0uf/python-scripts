#!/usr/bin/env python3
# coding: utf-8

"""
Backup rpi3 running mpd
"""

from utils import io

if __name__ == "__main__":
    TMP_PATH = "/tmp"
    HOME_PATH = "/home/pi"
    BACKUP_DIR = "backup-mpd"
    BACKUP_NAME = f"{BACKUP_DIR}.txz"
    BACKUP_PATH = f"{TMP_PATH}/{BACKUP_DIR}"
    BACKUP_HOME_PATH = f"{BACKUP_PATH}/_home"
    BACKUP_ETC_PATH = f"{BACKUP_PATH}/_etc"
    BACKUP_VAR_PATH = f"{BACKUP_PATH}/_var"
    BACKUP_SYSTEMD_PATH = f"{BACKUP_PATH}/_systemd"

    # Create a temp directory for backup
    io.cd(TMP_PATH)
    io.rm2([BACKUP_DIR, BACKUP_NAME])
    io.mkdir(BACKUP_PATH)

    # Backup home folder
    io.mkdir(BACKUP_HOME_PATH)
    io.cp_dir(f"{HOME_PATH}/mpd", f"{BACKUP_HOME_PATH}/mpd")
    io.cp_file(f"{HOME_PATH}/.zpreztorc", BACKUP_HOME_PATH)
    io.cp_file(f"{HOME_PATH}/.zshrc", BACKUP_HOME_PATH)

    # Backup /etc
    io.mkdir(BACKUP_ETC_PATH)
    io.cp_dir("/etc/nginx", f"{BACKUP_ETC_PATH}/nginx")
    io.cp_file("/etc/fstab", BACKUP_ETC_PATH)
    io.cp_file("/etc/mpd.conf", BACKUP_ETC_PATH)

    # Backup services
    io.mkdir(BACKUP_SYSTEMD_PATH)
    io.cp_file("/lib/systemd/system/mpd.service", BACKUP_SYSTEMD_PATH)

    # Backup /boot/config.txt
    io.cp_file("/boot/config.txt", BACKUP_PATH)

    # Compress & copy
    io.tar_xz(BACKUP_DIR, BACKUP_NAME)
    io.chown(BACKUP_NAME, "pi", "pi")
    io.chmod(BACKUP_NAME, 777)
    io.rm(BACKUP_DIR)
