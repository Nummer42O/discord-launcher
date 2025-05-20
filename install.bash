#!/usr/bin/bash

user_install=false
edit_startup=false

if ! valid_args=$(getopt --options ueh --longoptions user-install,edit-startup,help -- "$@"); then
  print_help "${0}"
  return 64;
fi

eval set -- "${valid_args}"
while true; do
  case "${1}" in
    -u | --user-install)
      user_install=true
      shift
      ;;
    -e | --edit-startup)
      edit_startup=true
      shift
      ;;
    -h | --help)
      echo "$0 [--user-install] [--edit-startup] [--help]"
      echo
      echo "Install discord launcher globally or per user."
      echo "Optionally also replace discord in the startup applications."
      echo "NOTE: Startup application replacement can only be done per user."
      exit 0
      ;;
    --)
      shift
      break
      ;;
  esac
done

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if ${user_install}; then
  install_location=~/.local/bin
  if ! [[ -d ${install_location} ]]; then
    mkdir -p "${install_location}"
  fi

  echo "Installing script in '${install_location}'."
  cp "${script_dir}/src/discord-launcher.py" "${install_location}"
  chmod +x "${install_location}"
else
  install_location=/usr/local/bin

  echo "Installing script in '${install_location}'."
  sudo cp "${script_dir}/src/discord-launcher.py" "${install_location}"
  sudo chmod +x "${install_location}"
fi

if ${edit_startup}; then
  echo "Adding to startup applications."
  env LAUNCHER_PATH="${install_location}/discord-launcher.py" \
    envsubst < "${script_dir}/discord-launcher.desktop.in" > ~/.config/autostart/discord-launcher.desktop

  echo "Disabling default discord autostart entry."
  sed -i -e 's/X-GNOME-Autostart-enabled=true/X-GNOME-Autostart-enabled=false/g' ~/.config/autostart/discord-stable.desktop
fi
