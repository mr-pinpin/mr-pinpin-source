#!/bin/bash
# Delivers the key, tool, config and README to each Mac, once. Hosts that are offline
# are retried by pinpin-store-macs.timer. The key travels only over ssh stdin. Apple
# Silicon kills unsigned binaries, so each Mac signs its own copy.
set -u
# macOS has no C.UTF-8, and ssh forwards LANG/LC_*; perl (shasum) then panics.
export LC_ALL=C LANG=C
STATE=/var/lib/pinpin-store/macs; SHARE=/usr/local/share/pinpin-store; KEY=/etc/pinpin-store/key
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=10 -i /root/.ssh/pinpin_mac_setup)
HOSTS=(pinpin-air pinpin-air-reverse pinpin-mini pinpin-migue anastasiia@100.126.246.54)
want=$(sha256sum "$KEY" | cut -d' ' -f1)
mkdir -p "$STATE"; missing=0

deliver() {
  local host=$1 arch hf
  arch=$("${SSH[@]}" "$host" 'uname -m') || return 1
  [ "$arch" = arm64 ] || arch=amd64
  hf=$("${SSH[@]}" "$host" 'export PATH=$PATH:/opt/homebrew/bin:$HOME/Library/Python/3.14/bin:$HOME/.local/share/pinpin-connect/hf-ssh/venv/bin; command -v hf || echo hf') || return 1
  "${SSH[@]}" "$host" 'umask 077; mkdir -p ~/.config/pinpin-store ~/.local/state/pinpin-store' || return 1
  local have
  have=$("${SSH[@]}" "$host" 'shasum -a 256 ~/.config/pinpin-store/key 2>/dev/null | cut -d" " -f1')
  if [ -z "$have" ]; then
    "${SSH[@]}" "$host" 'umask 077; cat > ~/.config/pinpin-store/key.tmp && mv -n ~/.config/pinpin-store/key.tmp ~/.config/pinpin-store/key' < "$KEY" || return 1
    have=$("${SSH[@]}" "$host" 'shasum -a 256 ~/.config/pinpin-store/key | cut -d" " -f1')
  fi
  if [ "$have" != "$want" ]; then echo "$host: key differs, left unchanged" >&2; return 1; fi
  "${SSH[@]}" "$host" 'umask 022; cat > ~/.config/pinpin-store/pinpin-store.tmp && chmod 755 ~/.config/pinpin-store/pinpin-store.tmp && /usr/bin/codesign -s - -f ~/.config/pinpin-store/pinpin-store.tmp 2>/dev/null && mv ~/.config/pinpin-store/pinpin-store.tmp ~/.config/pinpin-store/pinpin-store' < "$SHARE/pinpin-store-darwin-$arch" || return 1
  "${SSH[@]}" "$host" 'cat > ~/.config/pinpin-store/README.md' < "$SHARE/mac-README.md" || return 1
  printf '{"publicBucket":"miguelemosreverte/pinpin-vps-blobs","privateBucket":"miguelemosreverte/pinpin-vps-vault","host":"%s","hf":"%s","keyFile":"HOME/.config/pinpin-store/key","stateDir":"HOME/.local/state/pinpin-store","roots":[]}\n' "$(hostname)" "$hf" |
    "${SSH[@]}" "$host" 'sed "s#HOME#$HOME#g" > ~/.config/pinpin-store/config.json' || return 1
  # Delivered means this Mac decrypted the real log, not just that a file arrived.
  "${SSH[@]}" "$host" 'cd ~/.config/pinpin-store; rm -f ~/.local/state/pinpin-store/index.jsonl ~/.local/state/pinpin-store/index.jsonl.published; ./pinpin-store --config config.json pull-index && ./pinpin-store --config config.json status' 2>/dev/null |
    grep -aqE "index: [0-9]+ paths, [1-9][0-9]* verified" || return 1
}

for host in "${HOSTS[@]}"; do
  [ -e "$STATE/$host" ] && continue
  [ "$host" = pinpin-air-reverse ] && [ -e "$STATE/pinpin-air" ] && continue
  [ "$host" = pinpin-air ] && [ -e "$STATE/pinpin-air-reverse" ] && continue
  if deliver "$host"; then touch "$STATE/$host"; echo "delivered: $host"; else echo "pending: $host"; missing=1; fi
done
[ "$(ls "$STATE" | wc -l)" -ge 4 ] && systemctl disable --now pinpin-store-macs.timer 2>/dev/null
exit 0
