#!/bin/bash

set +x
pid="0"

handle_signal() {
  echo ""
  echo "Interrupt signal received!"
  if [ "x${pid}" != "x0" ]; then
    kill -SIGTERM "${pid}"
    wait "${pid}"
  fi
  exit 0
}

trap 'handle_signal' SIGINT SIGTERM SIGHUP SIGUSR1 SIGUSR2

print_help() {
  echo "Print help called!"
}

echo -e ""
echo -e "              %%%%%%%%%                  "
echo -e "               %%%%%%%%                  "
echo -e "                 %%%%%%                  "
echo -e "         %%%%%%%%%%%%%%%%%%%%%%          "
echo -e "         %%%%%%%%%%%%%%%%%%%%%%          "
echo -e "         %%%%%%%%%%%%%%%%%%%%%%          "
echo -e "                    %%%                  "
echo -e "                %%%%%%%                  "
echo -e "               %%%%%%%%                  "
echo -e "              %%%%%%%%%                  "
echo -e "              %%%%%%%%%                  "
echo -e "              %%%%%%%%%                  "
echo -e "              %%%%%%%%%%%                "
echo -e "               %%%%%%%%%%%%%%%           "
echo -e "                 #%%%%%%%%%%%%%          "
echo -e "                     %%%%%%%%%%          "
echo -e ""
echo " Welcome to the Turba Chakra docker container (v${TURBA_CONTAINER_VERSION})!"
echo ""

. /app/.venv/bin/activate
"$@" &
pid="${!}"
wait "${pid}"