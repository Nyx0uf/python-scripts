#!/usr/bin/env python3
# coding: utf-8

"""
Backup my PC
"""

from utils import common, io

if __name__ == "__main__":
    TMP_PATH = "/tmp"
    USER_HOME_PATH = "/home/nyxouf"
    USER_HOME_CONFIG_PATH = f"{USER_HOME_PATH}/.config"
    BACKUP_DIR = "backup-pc"
    BACKUP_NAME = f"{BACKUP_DIR}.txz"
    BACKUP_PATH = f"{TMP_PATH}/{BACKUP_DIR}"
    BACKUP_HOME_PATH = f"{BACKUP_PATH}/_home"
    BACKUP_HOME_CONFIG_PATH = f"{BACKUP_HOME_PATH}/_config"
    BACKUP_ETC_PATH = f"{BACKUP_PATH}/_etc"
    BACKUP_VAR_PATH = f"{BACKUP_PATH}/_var"

    # Create a temp directory for backup
    io.cd(TMP_PATH)
    io.rm2([BACKUP_DIR, BACKUP_NAME])

    # Backup ~
    # .config
    io.mkdir(BACKUP_HOME_CONFIG_PATH)
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/katerc", BACKUP_HOME_CONFIG_PATH)
    io.cp_dir(f"{USER_HOME_CONFIG_PATH}/bunkus.org", f"{BACKUP_HOME_CONFIG_PATH}/bunkus.org")
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/mkvtoolnix-guirc", BACKUP_HOME_CONFIG_PATH)
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/makemkvrc", BACKUP_HOME_CONFIG_PATH)
    io.cp_dir(f"{USER_HOME_CONFIG_PATH}/Transmission Remote GUI", f"{BACKUP_HOME_CONFIG_PATH}/Transmission Remote GUI")
    # mpv
    io.mkdir(f"{BACKUP_HOME_CONFIG_PATH}/mpv")
    io.cp_dir(f"{USER_HOME_CONFIG_PATH}/mpv/hrtf", f"{BACKUP_HOME_CONFIG_PATH}/mpv")
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/mpv/input.conf", f"{BACKUP_HOME_CONFIG_PATH}/mpv")
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/mpv/mpv.conf", f"{BACKUP_HOME_CONFIG_PATH}/mpv")
    io.cp_dir(f"{USER_HOME_CONFIG_PATH}/mpv/scripts", f"{BACKUP_HOME_CONFIG_PATH}/mpv")
    io.cp_dir(f"{USER_HOME_CONFIG_PATH}/mpv/shaders", f"{BACKUP_HOME_CONFIG_PATH}/mpv")
    # filezilla
    io.mkdir(f"{BACKUP_HOME_CONFIG_PATH}/filezilla")
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/filezilla/filezilla.xml", f"{BACKUP_HOME_CONFIG_PATH}/filezilla")
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/filezilla/layout.xml", f"{BACKUP_HOME_CONFIG_PATH}/filezilla")
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/filezilla/recentservers.xml", f"{BACKUP_HOME_CONFIG_PATH}/filezilla")
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/filezilla/sitemanager.xml", f"{BACKUP_HOME_CONFIG_PATH}/filezilla")
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/filezilla/trustedcerts.xml", f"{BACKUP_HOME_CONFIG_PATH}/filezilla")
    # Cantata
    io.mkdir(f"{BACKUP_HOME_CONFIG_PATH}/cantata")
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/cantata/cantata.conf", f"{BACKUP_HOME_CONFIG_PATH}/cantata")
    # beets
    io.mkdir(f"{BACKUP_HOME_CONFIG_PATH}/beets")
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/beets/config.yaml", f"{BACKUP_HOME_CONFIG_PATH}/beets")
    io.cp_file(f"{USER_HOME_CONFIG_PATH}/beets/music.blb", f"{BACKUP_HOME_CONFIG_PATH}/beets")
    # Misc
    io.cp_file(f"{USER_HOME_PATH}/.gitconfig", BACKUP_HOME_PATH)
    io.cp_file(f"{USER_HOME_PATH}/.nanorc", BACKUP_HOME_PATH)
    io.cp_file(f"{USER_HOME_PATH}/.ncmpcpp", BACKUP_HOME_PATH)
    io.cp_file(f"{USER_HOME_PATH}/.profile", BACKUP_HOME_PATH)
    io.cp_file(f"{USER_HOME_PATH}/.tmux.conf", BACKUP_HOME_PATH)
    io.cp_file(f"{USER_HOME_PATH}/.vimrc", BACKUP_HOME_PATH)
    io.cp_file(f"{USER_HOME_PATH}/.zlogout", BACKUP_HOME_PATH)
    io.cp_file(f"{USER_HOME_PATH}/.zpreztorc", BACKUP_HOME_PATH)
    io.cp_file(f"{USER_HOME_PATH}/.zshaliases", BACKUP_HOME_PATH)
    io.cp_file(f"{USER_HOME_PATH}/.zshrc", BACKUP_HOME_PATH)
    io.cp_dir(f"{USER_HOME_PATH}/.ssh", f"{BACKUP_HOME_PATH}/.ssh")
    io.cp_dir(f"{USER_HOME_PATH}/.vscode", f"{BACKUP_HOME_PATH}/.vscode")
    io.cp_dir(f"{USER_HOME_PATH}/.zprezto", f"{BACKUP_HOME_PATH}/.zprezto")

    # Backup /etc
    io.mkdir(BACKUP_ETC_PATH)
    io.cp_file("/etc/exports", BACKUP_ETC_PATH)
    io.cp_file("/etc/fstab", BACKUP_ETC_PATH)
    io.cp_file("/etc/mpd.conf", BACKUP_ETC_PATH)
    io.cp_dir("/etc/ssh", f"{BACKUP_ETC_PATH}/ssh")
    io.cp_dir("/etc/sysctl.d", f"{BACKUP_ETC_PATH}/sysctl.d")
    io.cp_dir("/etc/systemd", f"{BACKUP_ETC_PATH}/systemd")
    io.cp_dir("/etc/X11", f"{BACKUP_ETC_PATH}/X11")

    # Backup /var
    io.mkdir(f"{BACKUP_VAR_PATH}/mpd")
    io.cp_file("/var/lib/mpd/database", f"{BACKUP_VAR_PATH}/mpd")
    io.cp_dir("/var/lib/mpd/playlists", f"{BACKUP_VAR_PATH}/mpd/playlists")

    # Backup crontab
    CRON_ROOT = common.system_call("crontab -l")
    with open(f"{BACKUP_PATH}/crontab_root.txt", 'wb') as f:
        f.write(CRON_ROOT)
    CRON_ME = common.system_call("crontab -l -u nyxouf")
    with open(f"{BACKUP_PATH}/crontab_nyxouf.txt", 'wb') as f:
        f.write(CRON_ME)

    # Compress & copy
    io.chown(BACKUP_PATH, "nyxouf", "nyxouf")
    io.tar_xz(BACKUP_DIR, BACKUP_NAME)
    io.mv(BACKUP_NAME, f"/media/nyxouf/internal/{BACKUP_NAME}")
    io.chown(f"/media/nyxouf/internal/{BACKUP_NAME}", "nyxouf", "nyxouf")
    io.chmod(f"/media/nyxouf/internal/{BACKUP_NAME}", 777)
    io.rm(BACKUP_DIR)
