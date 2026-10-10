#!/bin/sh
# Local, predefined recovery protocol. Does not need the VPS or this chat to run.
wait_forever=false
check=false
case "${1-}" in
  --wait) wait_forever=true; shift ;;
  --check) check=true; shift ;;
esac
case "${1-}" in --) shift ;; esac
if [ "$#" -eq 0 ]; then set -- /usr/local/bin/codex-menu; fi

primary_routes='hostinger-vps hostinger-vps-public hostinger-vps-reality'
meeting_routes=''
route_file="${PINPIN_RECOVERY_ROUTES:-$HOME/.config/pinpin-connect/recovery-routes.conf}"
# Treat the cached policy as data, never executable shell. If it is damaged,
# retain the known anchor routes rather than preventing recovery altogether.
if [ -r "$route_file" ]; then
  if awk '
    /^[[:space:]]*($|#)/ {next}
    !/^(primary|meeting)[[:space:]]+[A-Za-z0-9][A-Za-z0-9._-]*[[:space:]]*$/ {exit 1}
    $1 == "primary" {count++}
    END {if (!count) exit 1}
  ' "$route_file"; then
    primary_routes=$(awk '$1 == "primary" {print $2}' "$route_file")
    meeting_routes=$(awk '$1 == "meeting" {print $2}' "$route_file")
  else
    echo 'Cached route policy is invalid; using the known recovery anchors.' >&2
  fi
fi

attempt_routes() {
  for route in $routes; do
    case "$route" in
      hostinger-vps) connect_timeout=5 ;;
      hostinger-vps-firebase) connect_timeout=20 ;;
      hostinger-vps-reality|hostinger-vps-rendezvous) connect_timeout=12 ;;
      *) connect_timeout=8 ;;
    esac
    echo "Trying $route..." >&2
    if $check; then
      ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout="$connect_timeout" \
        -o ServerAliveInterval=20 -o ServerAliveCountMax=3 "$route" hostname
    else
      ssh -t -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout="$connect_timeout" \
        -o ServerAliveInterval=20 -o ServerAliveCountMax=3 "$route" "$@"
    fi
    route_status=$?
    if $check; then
      if [ "$route_status" -eq 0 ]; then reachable=true; fi
    elif [ "$route_status" -ne 255 ]; then
      return "$route_status"
    fi
  done
  return 255
}

if $check; then
  reachable=false
  routes="$primary_routes $meeting_routes"
  attempt_routes "$@"
  if $reachable; then exit 0; else exit 255; fi
fi

routes="$primary_routes"
attempt_routes "$@"
result=$?
if [ "$result" -ne 255 ]; then exit "$result"; fi

echo 'Normal routes failed. Waiting 30 seconds, then trying our cached meeting routes.' >&2
sleep 30 || exit $?
routes="$meeting_routes"
attempt_routes "$@"
result=$?
if [ "$result" -ne 255 ]; then exit "$result"; fi

while :; do
  echo 'Waiting 60 seconds, then checking all agreed routes. Ctrl-C cancels.' >&2
  sleep 60 || exit $?
  routes="$meeting_routes $primary_routes"
  attempt_routes "$@"
  result=$?
  if [ "$result" -ne 255 ]; then exit "$result"; fi
  if ! $wait_forever; then break; fi
done

echo 'No agreed route answered. See ~/PINPIN-RECOVERY.txt for the offline plan.' >&2
echo 'Switch to mobile data, or use the Hostinger browser console. Do not delete SSH host keys.' >&2
exit 255
