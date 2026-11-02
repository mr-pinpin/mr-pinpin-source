# pinpin-store

Backs up a whole machine to Hugging Face. Everything is public unless the owner says
otherwise or it is plainly a credential, such as an API key, which goes private. Every blob is encrypted on this machine first, so a
misclassified file exposes nothing. An append-only log is the source of truth; the
local index is its replay, and readers never need to know which bucket holds a blob.

```sh
pinpin-store init              # create the key and both buckets
pinpin-store flush             # report what would upload
pinpin-store flush --apply     # upload, verify from a fresh download, record
pinpin-store ls /root/work     # both | local | remote | changed, offline
pinpin-store check /root/work  # exit 1 if anything is not protected
pinpin-store get /path/file    # restore; never overwrites
pinpin-store evict DIR         # report what could be freed
pinpin-store get DIR           # restore every remote-only file under DIR
pinpin-store pull-index        # rebuild the index from the bucket log
```

The key is the only way to read the backup. Keep a copy off this machine.

Only `evict --apply --key-is-off-machine` deletes local files, and only inside the
configured `evictable` trees, after re-hashing each one against its proven blob.
Evicted paths still show in `pinpin-store ls` as `remote`; ordinary `ls` no longer
sees them. Everything else never deletes or changes local files. A blob counts only after a
fresh download decrypts to the expected hash; sensitive files never spill into the
public bucket when the private tier is full, they stay on disk, reported as
unprotected; sensitive files upload only to a bucket confirmed private. Files open
for writing can be captured mid-update.

## Ordinary commands: the mount

The log is the write side. `pinpin-store serve` is the read side: it projects the
log into a directory tree and mounts each tree in `mounts` over itself, so plain
`ls`, `find`, `stat`, `du` and `df` work on evicted files with no network, and
opening one downloads and verifies it first. Reads go to a cache of
`readCacheBytes` (2 GiB) under the state directory, so a grep across a tree never
refills the disk; opening for writing puts the file back in place.
Reads ahead like a disk does, using the index: a second cold read in a directory
within a minute fetches the rest of it, 8 at a time; two scanned sibling directories
fetch the following ones too, in walk order. Files over 32 MiB and anything past
512 MiB in flight are left to be read on demand. The daemon logs how many guesses
were used (`prefetch: fetched N, used M`). A grep over 251 moved files took 12.6 s
instead of 86 s; 98% of fetched-ahead files were read. `df` reports `viewBytes`. With
`keyIsOffMachine` set, it evicts proven files least-recently-read first to keep
`keepFreeBytes` free. A stopped daemon gives `Transport endpoint is not connected`,
never empty data. Writes land on the local disk until a flush proves them, so one
burst larger than the free space still fails with ENOSPC.

`rawRoot` is a private bind mount of `/` that exposes the real disk under the mounts.
**Never `rm -rf` it or a parent of it: that deletes the whole system, and
`--one-file-system` does not help because it is the same filesystem.** Unmount it.
It must also stay outside every temporary and state directory. Tools that walk `/`
will see it, so exclude it.

Uploads shell out to `hf` because bucket uploads use the Xet protocol, which has no
Go client. Tests use a fake `hf` executable: `go test ./...`. Install with
`go build -o /usr/local/bin/pinpin-store .`, then copy `config.example.json` to
`/etc/pinpin-store/config.json` and the units in `systemd/` to `/etc/systemd/system`.
