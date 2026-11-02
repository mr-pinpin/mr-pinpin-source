# pinpin-store on the Mr. PinPin VPS

The tool itself now lives in its own repository,
[miguelemosreverte/hfstore](https://github.com/miguelemosreverte/hfstore): an
encrypted whole-machine backup to Hugging Face buckets, with a FUSE mount that keeps
cold files remote. It is pinpin-store under a new name, with the same formats, so it
reads and writes this VPS backup unchanged. `/usr/local/bin/pinpin-store` is a link to
`/usr/local/bin/hfstore`.

This folder keeps only what is specific to this VPS:

| File | Purpose |
|---|---|
| `systemd/pinpin-store.service`, `.timer` | daily flush, run by `hfstore` |
| `systemd/pinpin-store-serve.service` | the mounts listed in `/etc/pinpin-store/config.json` |
| `activate.sh`, `systemd/pinpin-store-activate.*` | one-time switch-on of the mounts after the first proven flush |
| `deploy-macs.sh`, `systemd/pinpin-store-macs.*`, `mac-README.md` | copy the key and a macOS build to each Mac until every Mac proves it can decrypt |

Install or update the tool:

```sh
git clone https://github.com/miguelemosreverte/hfstore && cd hfstore
go build -o /usr/local/bin/hfstore .
for a in arm64 amd64; do GOOS=darwin GOARCH=$a go build -o /usr/local/share/pinpin-store/pinpin-store-darwin-$a .; done
systemctl restart pinpin-store-serve.service
```

`rawRoot` (`/mnt/pinpin-store-raw`) is a bind mount of `/`. **Never `rm -rf` it or a
parent of it: that deletes the whole system.** See the hfstore README.
