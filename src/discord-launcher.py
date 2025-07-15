#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import datetime
import tempfile
import requests
import pathlib
import logging
import shutil
import signal
import re, sys

from typing import Optional


def sendNotification(msg: str, error: bool = False):
    subprocess.Popen(
        [
            "notify-send",
                "-i", "/usr/share/discord/discord.png",
                "-u", "critical" if error else "low",
                "Discord Launcher",
                msg
        ],
    ).wait()

def removeOldLogs(logDir: str, olderThen: int = 14):
    subprocess.Popen(
        [
            "find",
                f"{logDir}",
                "-regex", ".*\.log",
                "-type", "f",
                "-mtime", f"+{olderThen}",
                "-exec", "rm", "{}", "+"
        ]
    ).wait()

def main() -> int:
    logDir = pathlib.Path.home() / ".local/share/discord-launcher/"
    logDir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("discord-launcher")
    handler = logging.FileHandler(logDir / f"{datetime.datetime.now()}.log", "w")
    handler.setFormatter(
        logging.Formatter(
            fmt="[%(asctime)s][%(levelname) 8s] %(name)s: %(message)s",
            datefmt="%d.%m.%Y %H:%M:%S"
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    removeOldLogs(logDir)

    # setup
    discordPath = shutil.which("discord")
    timeoutTime = (
        datetime.datetime.now() + datetime.timedelta(seconds=60)
    )
    upToDatePattern = re.compile(
        r"^.* \[Modules\] Host is up to date.$"
    )
    needsUpdatePattern = re.compile(
        r"^.* \[Modules\] Host update is available. Manual update required!$"
    )
    discordDownloadLink = "https://discord.com/api/download?platform=linux&format=deb"
    vencordDownloadLink = "https://github.com/Vendicated/VencordInstaller/releases/latest/download/VencordInstallerCli-Linux"


    # start initial process
    discordProcess = subprocess.Popen(
        [],
        executable=discordPath,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # monitor output
    needsUpdate: Optional[bool] = None
    while (
            discordProcess.poll() is None and
            datetime.datetime.now() < timeoutTime
        ):
        logLine = discordProcess.stdout.readline()
        if not logLine:
            continue
        logger.debug(logLine.rstrip('\n'))

        if re.match(needsUpdatePattern, logLine):
            logger.info("Discord needs to be updated.")
            needsUpdate = True
            break
        if re.match(upToDatePattern, logLine):
            logger.info("Discord is up to date.")
            needsUpdate = False
            break

    # remove old process since the pipe brings along problems with JS
    logger.debug("Interrupting old process.")
    discordProcess.send_signal(signal.SIGINT)
    discordProcess.wait()
    logger.debug("Old process interrupted.")

    # if the check ran inconclusive, don't do anything further
    if needsUpdate is None:
        logger.error("Could not determine update status, please refer to the logs above.")
        return 1

    # if the check determined that a new version is available, install it
    if needsUpdate:
        with (tempfile.NamedTemporaryFile("wb", prefix="discord", suffix=".deb") as discordDebFile,
              tempfile.NamedTemporaryFile("wb", prefix="vencord", suffix="") as vencordUpdaterFile,
              tempfile.NamedTemporaryFile("w", prefix="bothcord", suffix=".bash") as updateScriptFile):
            # download discord install/update .deb-file
            discordDebResponse = requests.get(
                discordDownloadLink,
                timeout=30
            )
            if not discordDebResponse.ok:
                logger.fatal(
                    "Failed to download discord update: %d: %s",
                    discordDebResponse.status_code,
                    discordDebResponse.content.decode(errors="replace")
                )
                sendNotification("Failed to download update. See log file for more.", True)
                return 2

            # write deb package to temp file
            discordDebFile.write(discordDebResponse.content)
            discordDebFile.flush()

            # update vencord updater
            vencordUpdaterResponse = requests.get(
                url=vencordDownloadLink,
                timeout=30
            )
            if not vencordUpdaterResponse.ok:
                logger.fatal(
                    "Failed to downoad vencord updater file: %d: %s",
                    vencordUpdaterResponse.status_code,
                    vencordUpdaterResponse.content.decode(errors="replace")
                )
                sendNotification("Failed to download vencord updater. See log file for more.", True)
                return 2

            # write sh file to temp file
            vencordUpdaterFile.write(vencordUpdaterResponse.content)
            vencordUpdaterFile.flush()

            # temporarily bundle both calls in a bash script
            updateScriptFile.writelines([
                "#! /usr/bin/bash",
                f"dpkg -i {discordDebFile.name} || exit",
                f"{vencordUpdaterFile.name} -branch stable -repair || exit"
            ])
            updateScriptFile.flush()

            # install update with elevated rights
            discordUpdateProcess = subprocess.Popen(
                ["pkexec", "/usr/bin/bash", updateScriptFile.name],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            with discordUpdateProcess.stdout:
                for line in iter(discordUpdateProcess.stdout, b''):
                    logger.debug("[Update Subprocess] %r", line)
            if discordUpdateProcess.wait() != 0:
                logger.fatal(
                    "Failed to install discord update (discord update file: %s, vencord updater: %s).",
                    discordDebFile.name,
                    vencordUpdaterFile.name
                )
                sendNotification("Failed to install update. See log file for more.", True)
                return 3
        sendNotification("Successfully updated Discord and Vencord.")

    # relaunch discord
    logger.debug("Launching discord..")
    subprocess.Popen(
        [],
        executable=discordPath,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )

    return 0;

if __name__ == "__main__":
    sys.exit(main())

