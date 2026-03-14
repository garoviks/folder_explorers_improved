# Create CBZ v2 (makecbz.py)

A specialized command-line utility for merging multiple comic archives into a single organized volume.

## Key Features
- **Multi-Format Support**: Extracts `.cbz`, `.cbr`, `.zip`, and `.rar` files automatically using system utilities (`unzip`, `unrar`).
- **Flexible Pattern Matching**: Accepts wildcard patterns (e.g., `Spider-Man*`) to target specific issue ranges.
- **Smart Cleanup**:
  - Automatically deletes extracted temporary folders upon success.
  - Deletes original archives once the merge is confirmed successful.
- **Simulation Mode**: Includes a `--dry-run` flag to preview every action (extraction, compression, deletion) without touching the filesystem.
- **Clean Environment**: Prevents the creation of even empty "working" or "output" directories when running in dry-run mode.
- **Ordered Merging**: Sorts files alphabetically/numerically before extraction to ensure the pages appearing in the final archive follow the correct issue sequence.

## Requirements
- `unzip`
- `unrar`
- `zip`
