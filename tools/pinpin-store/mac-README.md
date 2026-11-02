# pinpin-store on this Mac

The VPS `hostinger-vps` backs itself up to Hugging Face as encrypted blobs. This
folder lets any Mac browse that backup and restore files from it. Macs only read:
do not run `flush`, `evict` or `init` here.

| File | Purpose |
|---|---|
| `key` | The encryption key. Without it the backup cannot be read. |
| `config.json` | Bucket names and paths for this Mac |
| `pinpin-store` | The command line tool |

**Keep `key` private: never commit it, paste it into a chat, or upload it.** Every
Mac holds the same key, and the public bucket is only safe while the key stays secret.

## Use

```sh
alias pinpin-store='~/.config/pinpin-store/pinpin-store --config ~/.config/pinpin-store/config.json'

pinpin-store pull-index                  # first time: rebuild the index from the bucket
pinpin-store status                      # bucket usage and index totals
pinpin-store ls /root/work               # browse the VPS, no network needed
pinpin-store get /root/work/a.png --out ~/Downloads/a.png
```

To see newer backups, remove the old index and pull it again:

```sh
rm ~/.local/state/pinpin-store/index.jsonl*
pinpin-store pull-index
```

## If the VPS is gone

The buckets are `miguelemosreverte/pinpin-vps-blobs` (public: blobs and the encrypted
log) and `miguelemosreverte/pinpin-vps-vault` (private: sensitive files). Everything is
on Hugging Face, so this folder is all you need to get it back. Restore a whole folder
with `pinpin-store get DIR` on a Linux machine running as root.

The source is `tools/pinpin-store/` in `mr-pinpin/mr-pinpin-source`, and it explains
the design in its own README.
