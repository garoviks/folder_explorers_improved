# Action Explorer — Development Guide

## Project Overview

**Action Explorer** is a self-contained Python web server + browser UI for managing a large personal comic book collection stored as `.cbr` and `.cbz` archive files.

### Core Pain Points Solved
1. **Batch conversion** — Merge multiple .cbr/.cbz issue files into single volume archives (e.g., 6 issue #1-6 files → one v01 volume)
2. **Browser + housekeeping** — Navigate folder structure, rename files/folders, audit which series are ready to merge

### Architecture
- Single-file Python HTTP server (no external frameworks, no database)
- Dark-themed web UI served at `http://localhost:8123/`
- Linux-only (Kubuntu/Debian), no Windows/macOS support
- Single user, no authentication needed

### Key Technologies
- **Python:** 3.10+ (stdlib only — no pip packages)
- **System dependencies:** `unrar` (RAR5 support), `unzip`, `zip`
- **Browser:** Firefox on Linux
- **Git:** GitHub repository at https://github.com/garoviks/folder_explorers_improved

---

## Project Structure

```
├── action_explorer.py          # Active version (v12) — Main application
├── action_explorer_vNN.py      # Version history (v01, v02, v04-v12)
├── makecbz.py                  # Legacy CBZ creation utility (v02)
├── action_explorer_requirements.md
├── action_explorer_spec.md
├── action_explorer_requirements.html
├── DEVELOPMENT.md              # This file
└── [images, old docs]
```

---

## Architecture & Components

### Backend (Python HTTP Server)

**CustomHandler Class**
- Extends `SimpleHTTPRequestHandler` with three main overrides:
  - `do_GET()` — Serves files, directories, intercepts `/view_csv?file=<path>`
  - `do_POST()` — Handles: rename, create_cbz_direct, check_subfolders
  - `list_directory()` — Generates dark-themed HTML directory listing

**Core Functions**

**Filename Parsing:**
- `parse_filename(filename)` → `{series, subtitle, year}` dict
- Supports: `Series 01 (of 05) - Subtitle (2025)` and `Series (001) - Subtitle (2025)` formats
- Extracts 4-digit year, strips publisher tags like `(Digital)`

**Volume Detection:**
- `is_volume(name)` → bool
- Regex: `/\b(?:v|vol|book|t)\.?\s*\d+|TPB|Omnibus|Collection|Graphic\s*Novel|GN|HC|Scanlation|Complete/i`
- Prevents volumes from being selected in batch operations

**CBZ Creation:**
- `create_cbz_direct(abs_path, files, outname)` → (bool, log_str)
- 6-step process:
  1. Create working folder
  2. Extract files (alphabetically ordered for correct page sequence)
  3. Zip extracted content
  4. Move CBZ to destination
  5. Delete source files (only on success)
  6. Cleanup working folder
- Supports `.cbr` (unrar) and `.cbz` (unzip)
- Only deletes source files on **success**; keeps originals on failure

**Subfolder Scanning:**
- `check_folder_for_cbz(folder_path)` → list of dicts (depth-2 recursive scan)
- Groups comic files by series, flags volumes, assigns status per group
- Generates CSV with: path, series, file_count, volumes_skipped, status, proposed_outname, has_deeper_subfolders, files

**CSV Rendering:**
- `render_csv_as_html(csv_path)` → HTML string
- Dark theme, sortable columns, filterable by status, clickable folder/series links

### Frontend (JavaScript in HTML)

**State Variables**
- `selectedFiles` (Set) — currently selected non-volume files
- `pendingCBZParams` — stores action details during countdown
- `cbzCountdownTimer`, `cbzCountdownInterval` — 4-second countdown before CBZ creation

**Key JS Functions**
- `isVolume(name)` — mirror of Python regex
- `parseFilename(filename)` — mirror of Python parser (supports both issue formats)
- `getNextVolumeNumber(series)` → 1, 2, 3... (scans existing .cbz files in DOM for highest v##)
- `buildOutname(parsed)` → "Series v03 - Subtitle (2025)"
- `prepareCreateCBZ()` — validation, warning, countdown start
- `proceedCBZ()` — POST to server, handles 10s reload countdown on success
- `checkSubfolders4CBZ()` — POST scan action, shows CSV view options

**UI Features**
- **Rubber-band selection** — click-drag on table background, auto-scroll at viewport edges
- **Volume auto-deselect** — selecting a volume shows warning banner, unchecks item
- **Implicit fallback** — if no explicit selections, all non-volume files in folder treated as selected
- **Scroll restoration** — pressing Back highlights folder you came from, auto-scrolls

---

## Version History

| Version | Key Changes |
|---------|------------|
| v01-v03 | Initial development, type hints |
| v04-v08 | Progressive improvements |
| v09 | Major fix: replaced 7z with unrar + unzip (fixes RAR5 error); fixed rename button |
| v10 | Unknown specifics |
| v11 | Most recent stable baseline |
| v12 | **Current:** Fixed parse_filename() to recognize issue numbers in parentheses (e.g., "3W3M (001)") — prevents false multi-group warnings |

---

## Running the Application

### Start Server
```bash
python3 action_explorer.py [target_dir]
```
- `target_dir` optional, defaults to `.`
- Access at: `http://localhost:8123/`
- Stop with: `Ctrl+C`

### Requirements
- Python 3.10+
- System tools: `unrar`, `unzip`, `zip`

### No External Dependencies
- Uses Python stdlib only
- No pip packages required
- No web frameworks or databases

---

## API Endpoints

### POST `/` (JSON body)

**Action: rename**
```json
{
  "action": "rename",
  "abs_path": "/path/to/folder",
  "old_name": "old_filename",
  "new_name": "new_filename"
}
```

**Action: create_cbz_direct**
```json
{
  "action": "create_cbz_direct",
  "abs_path": "/path/to/folder",
  "files": ["file1.cbr", "file2.cbz"],
  "outname": "Series v03 - Subtitle (2025)"
}
```

**Action: check_subfolders**
```json
{
  "action": "check_subfolders",
  "abs_path": "/path/to/folder"
}
```

### GET `/view_csv?file=<absolute_path>`
Returns CSV as styled HTML table with sortable columns, filters, and status badges.

---

## File Selection Logic

### Volume Detection
Files matching the volume pattern are automatically excluded:
- Patterns: `v##`, `vol##`, `TPB`, `Omnibus`, `Collection`, `Graphic Novel`, `GN`, `HC`, `Scanlation`, `Complete`
- User sees warning banner when volumes are auto-deselected

### Implicit Selection Fallback
- If user clicks "Create CBZ" with **no explicit selections**, all non-volume files in the folder are treated as selected
- Prevents accidental empty selections

### Mixed Series Detection
- If selected files belong to >1 detected series, creation is blocked with warning
- Series detection from filename parsing

---

## Filename Parsing Examples

**Standard Format:**
```
Input:  "The Cold Witch 01 (of 05) - A Tale of the Shrouded College (2025) (Digital).cbr"
Output: {series: "The Cold Witch", subtitle: "A Tale of the Shrouded College", year: "2025"}
Result: "The Cold Witch v03 - A Tale of the Shrouded College (2025)"
```

**Parenthesized Issue Number (v12 fix):**
```
Input:  "3W3M (001) - Fable (2021) (digital-Empire).cbr"
Output: {series: "3W3M", subtitle: "Fable", year: "2021"}
Result: "3W3M v01 - Fable (2021)"
```

---

## Development Notes

### Naming Convention
- Versions stored as `action_explorer_vNN.py`
- Active version is typically `action_explorer.py` or the highest version number

### Making Changes
1. Test thoroughly in v12 before pushing
2. For new features/fixes, create a new version file: `action_explorer_v13.py`
3. Commit and document the fix in this file
4. Update version history table above

### Thread Safety
- All subprocess calls use `cwd=` parameter, never `os.chdir()`
- Prevents thread-safety issues in HTTP server context

### Error Handling
- CBZ creation errors: logs detailed error, keeps source files, cleans up working folder
- Rename errors: returns error JSON, user must retry
- CSV scan errors: continues scanning, reports partial results

---

## Testing Checklist

Before committing changes:
- [ ] Directory listing displays correctly (folders first, alphabetical)
- [ ] Volume detection works (auto-deselect warning shown)
- [ ] Select/Deselect All button toggles correctly
- [ ] Rubber-band selection works, respects auto-scroll
- [ ] CBZ creation with 2+ files succeeds
- [ ] CBZ creation with >6 files shows confirmation dialog
- [ ] Mixed series detection blocks creation
- [ ] Rename button works for files and folders
- [ ] CSV scan completes without errors
- [ ] Scroll restoration highlights correct folder on Back
- [ ] Page reloads after successful CBZ creation (10s countdown)
- [ ] Errors don't auto-reload, keep output visible

---

## GitHub Repository

**URL:** https://github.com/garoviks/folder_explorers_improved

All changes are version-controlled. Use:
```bash
git status          # Check uncommitted changes
git diff            # Review changes before commit
git log --oneline   # See commit history
git push            # Push to GitHub
```

---

## External References

- **Requirements:** See `action_explorer_requirements.md` for full feature breakdown
- **Specification:** See `action_explorer_spec.md` for technical implementation details
- **Legacy Tool:** `makecbz.py` (v02) — earlier command-line CBZ creation utility (not used by current version)

---

**Last Updated:** 2026-04-05  
**Current Version:** v12  
**Author:** @garoviks
