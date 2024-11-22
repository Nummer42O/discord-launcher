# discord-lanuncher

Simple auto-updater for Discord on Linux.

> [!NOTE]
> This only works if Discord is installed via the debian files available on Discords own website.

## How it works

Discord gets started initially with an output pipe so the logs can be monitored.
If the logs match the pattern `^.* \[Modules\] Host update is available. Manual update required!$`, the Debian file for the update will get downloaded and installed. As this step needs super user privilages, pkexec is used.
In any case, the Discord instance will be killed and restarted without piping. This is necessary as it seemed that Electron did not like to remain in that state.

Logs get saved to `~/.local/share/discord-launcher/<datetime>.log`.

## Installation

For convenience there is a install script that can be executed directly.
For more info on how it works, use the `-h` or `--help` option.

The installer copies the main script to `~/.local/bin/` for user installation or `/usr/local/bin/` for global installation.
If requested, it also places a ".desktop" file in the users autostart directory (`~/.config/autostart/`) and disables discords autostart by setting `X-GNOME-Autostart-enabled=false`.

## TODO

- Use customized pkexec message or use a different (graphical) way to elevate rights.
