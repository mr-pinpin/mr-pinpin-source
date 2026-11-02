#!/bin/bash
# Turns on the mount once it is safe: the first full flush succeeded and at least one
# Mac has proven it can decrypt the backup. Reclaiming space starts only after that.
set -u
LOG=/var/lib/pinpin-store/activate.log; CONFIG=/etc/pinpin-store/config.json; RAW=/mnt/pinpin-store-raw
TREES=(/root/.cache/mr-pinpin /root/.local/share/pinpin-production)
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }

[ "$(ls /var/lib/pinpin-store/macs 2>/dev/null | wc -l)" -ge 1 ] || { say "waiting: no Mac has proven the key"; exit 0; }
# A oneshot unit reports "activating" while it runs, and is-active only matches "active".
[ "$(systemctl show -p ActiveState --value pinpin-store.service)" = inactive ] || { say "waiting: flush running"; exit 0; }
[ "$(systemctl show -p Result --value pinpin-store.service)" = success ] || { say "waiting: last flush did not succeed"; exit 0; }
last=$(journalctl -u pinpin-store.service --no-pager -o cat -n 40 | grep -a '^applied:' | tail -1)
# Remaining bytes stay above zero while the private tier is full, and evict only ever
# touches proven files, so a successful run that finished is the signal.
[ -n "$last" ] || { say "waiting: no finished flush in the journal"; exit 0; }

python3 - "$CONFIG" "$RAW" <<'P'
import json,sys
path,raw=sys.argv[1:3]; c=json.load(open(path))
c.update(rawRoot=raw,mounts=["/root/.cache/mr-pinpin","/root/.local/share/pinpin-production"],viewBytes=4000000000000,keyIsOffMachine=True)
json.dump(c,open(path,"w"),indent=2)
P
systemctl enable --now pinpin-store-serve.service
sleep 10
for tree in "${TREES[@]}"; do
  if [ "$(findmnt -no FSTYPE "$tree")" != fuse.pinpin-store ] || ! ls "$tree" >/dev/null; then
    say "FAILED: $tree did not mount; stopping serve"
    systemctl disable --now pinpin-store-serve.service
    python3 - "$CONFIG" <<'P'
import json,sys
c=json.load(open(sys.argv[1]))
for k in ("rawRoot","mounts","keyIsOffMachine"): c.pop(k,None)
json.dump(c,open(sys.argv[1],"w"),indent=2)
P
    systemctl disable --now pinpin-store-activate.timer
    exit 1
  fi
done
say "mounted ${TREES[*]}; reclaim is on"
systemctl disable --now pinpin-store-activate.timer
