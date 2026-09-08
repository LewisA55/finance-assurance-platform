# Private consumer-product backups

Excel and Power BI authoring binaries are deliberately excluded from the public
Git history. They therefore need a separate private recovery copy before any
workspace cleanup or public release operation.

Create an integrity-listed ZIP in an external private location:

```bash
python scripts/create_private_backup.py --destination D:/private-backups --label pre-public
```

The destination must be outside this repository. The archive contains ignored
Excel and Power BI work/exports plus compact build manifests, detached digests
and checksum inventories. `backup-manifest.json` records every relative path,
byte count, SHA-256 digest and the current Git commit. A detached `.sha256` file
authenticates the ZIP itself.

The script does not upload, delete or restore files. Store the ZIP in a private,
access-controlled location and test extraction before deleting any local
authoring binary. Large regenerated source populations remain recoverable from
the documented pipeline rather than being copied into this archive.
