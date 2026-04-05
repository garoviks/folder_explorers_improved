# action_explorer — Full Specification
## For re-creating `action_explorer_v11.py` from scratch

---

## Overview

A single-file Python 3 HTTP web server (`http.server`) that serves an interactive dark-themed directory browser at `http://localhost:8123/`.

Designed for managing comic book archives (.cbz/.cbr) on Linux (Kubuntu/Debian).

**Dependencies (system):** `unrar`, `unzip`, `zip`  
**No pip packages required.**

---

## 1. Entry point & startup

```
python3 action_explorer.py [target_dir]
```

- `target_dir` optional, defaults to `.`
- `os.chdir(target_dir)` before starting server
- Port: `8123`
- Graceful shutdown on `KeyboardInterrupt` — call `httpd.server_close()`

---

## 2. Server class: `CustomHandler(SimpleHTTPRequestHandler)`

Override three methods: `do_GET`, `do_POST`, `list_directory`.

---

## 3. GET requests

### 3a. `/view_csv?file=<absolute_path>`
Intercept before calling `super().do_GET()`.

- Read the CSV at the given absolute path
- Call `render_csv_as_html(csv_path)` and return as `text/html`
- Return 404 if file not found

### 3b. All other GET
Delegate to `super().do_GET()` — serves files normally including directory listings.

---

## 4. POST requests

All POSTs receive JSON body: parse `Content-Length` header, read body, `json.loads`.  
Dispatch on `action` field.

### 4a. `action = "rename"`
Fields: `abs_path`, `old_name`, `new_name`

- `os.rename(abs_path/old_name, abs_path/new_name)`
- Return `{"success": true}` or `{"error": "..."}` with HTTP 500

### 4b. `action = "create_cbz_direct"`
Fields: `abs_path`, `files` (list of filenames), `outname` (no extension)

Call `create_cbz_direct(abs_path, files, outname)`.  
Return `{"output": log_string, "success": bool}`

### 4c. `action = "check_subfolders"`
Fields: `abs_path`

Call `check_folder_for_cbz(abs_path)`, write CSV, return summary + view URL.  
Return `{"output": summary, "csv_path": path, "view_url": "/view_csv?file=..."}`

---

## 5. Python functions

### 5a. Constants

```python
COMIC_EXTS = {'.cbz', '.cbr', '.zip', '.rar'}

VOLUME_PATTERN = re.compile(
    r'\b(?:v|vol|book|t)\.?\s*\d+|TPB|Omnibus|Collection|Graphic\s*Novel|GN|HC|Scanlation|Complete',
    re.IGNORECASE
)

STATUS_COLOURS = {
    'ready': '#2e7d32', 'cbz_exists': '#1565c0',
    'single_file': '#f9a825', 'no_comics': '#424242', 'deeper_only': '#6a1fa2'
}

STATUS_LABELS = {
    'ready': 'Ready', 'cbz_exists': 'CBZ exists',
    'single_file': 'Single file', 'no_comics': 'No comics', 'deeper_only': 'Deeper only'
}
```

### 5b. `is_volume(name: str) -> bool`
Return `True` if `VOLUME_PATTERN` matches `name`.

### 5c. `parse_filename(filename: str) -> dict`
Strip extension. Extract:
- `year`: first `(YYYY)` pattern found
- `series`: everything before the issue number block — supports two formats:
  - `\s+#?\d+(\s*\(of\s*\d+\))?` — space + optional hash + digits (e.g. `Series 01`)
  - `\s+\(\d{1,3}\)` — number in parentheses, 1–3 digits (e.g. `Series (001)`)
- `subtitle`: text after ` - ` following issue block, with year tags and `(Word)` tags stripped

Return `{'series': str, 'subtitle': str|None, 'year': str|None}`

Examples:
```
"The Cold Witch 01 (of 05) - A Tale of the Shrouded College (2025) (Digital).cbr"
→ { series: "The Cold Witch", subtitle: "A Tale of the Shrouded College", year: "2025" }

"3W3M (001) - Fable (2021) (digital-Empire).cbr"
→ { series: "3W3M", subtitle: "Fable", year: "2021" }
```

### 5d. `build_outname(parsed: dict) -> str`
Format: `"{series} v01"` — then append `" - {subtitle}"` if present, then `" ({year})"` if present.

Note: `v01` is the Python fallback only. The JS version dynamically detects the next volume number (see JS section).

### 5e. `create_cbz_direct(abs_path, files, outname) -> tuple[bool, str]`

6-step process with verbose logging. Each log line prefixed with `✔`, `✖`, or `·`.

**Step 1 — Working folder**
- Path: `abs_path/outname/`
- If already exists: remove with `shutil.rmtree`, recreate

**Step 2 — Extract each selected file**
- Sort `files` alphabetically
- For each file, create subfolder `working_dir/{stem}/`
- `.cbr`/`.rar`: `unrar e -o+ -inul <src> <subdir>/`
- `.cbz`/`.zip`: `unzip -o -q <src> -d <subdir>`
- Log each extracted filename
- If exit code != 0: log error, raise RuntimeError (stops process, triggers cleanup)

**Step 3 — Zip working folder**
- `zip -r <working_dir/outname.cbz> .` run with `cwd=working_dir`
- Log resulting file size (KB/MB/GB)

**Step 4 — Move CBZ to abs_path**
- Remove existing CBZ at destination if present
- `shutil.move(cbz_in_working, cbz_final)`

**Step 5 — Delete original source files**
- Delete each file in `files` list
- Log success or `OSError` per file — do NOT abort on failure

**Step 6 — Cleanup**
- `shutil.rmtree(working_dir)`

On any exception: log failure, best-effort rmtree of working_dir, return `(False, log)`.

### 5f. `check_folder_for_cbz(folder_path: str) -> list[dict]`

Scan subfolders **up to 2 levels deep**. Start at depth=1 for immediate subfolders.

For each folder scanned:
- List files with COMIC_EXTS extensions
- Skip `is_volume()` files → count in `volumes_skipped`
- Group remaining by `parse_filename()['series']`
- For each series group:
  - Status: `cbz_exists` if a `.cbz` containing the series name exists, else `ready` if ≥2 files, else `single_file`
  - `proposed_outname`: `build_outname(parse_filename(first_file))`
- If folder has no comics: status `no_comics`
- At depth=2, if subdirs exist: set `has_deeper_subfolders=True`
- Folder with only subdirs and no comics at depth=2: status `deeper_only`
- Recurse into subdirs only if depth < 2

CSV columns: `path`, `series`, `file_count`, `volumes_skipped`, `status`, `proposed_outname`, `has_deeper_subfolders`, `files` (pipe-separated)

CSV filename: `{current_folder_name}_checked.csv` saved into `abs_path`.

### 5g. `render_csv_as_html(csv_path: str) -> str`

Dark-themed HTML table from a `*_checked.csv` file.

Features:
- Summary pill badges at top (count per status, colour-coded)
- Filter buttons per status (All / Ready / CBZ exists / Single file / No comics / Deeper only)
- Sortable columns (click header — numeric cols sort numerically, text alphabetically, toggle asc/desc)
- Status column: coloured badge span
- Path column: clickable link to folder in file browser (relative URL from `os.getcwd()`)
- Series column: series name + small grey link below it pointing to `path/series/` subfolder
- `has_deeper_subfolders`: shown as `✓`
- `← Back` link using `history.back()`

---

## 6. `list_directory` — HTML page generation

Dark theme. Build page as `list[str]` joined and encoded.

### 6a. CSS classes needed
- `body`: dark bg `#121212`, light text
- `table`: `#1e1e1e` bg, rounded, shadow
- `th`: `#2c2c2c`, sortable feel
- `tr:hover`: `#2a2a2a`
- `.dir`: green `#81c784` for folder links
- `.count-btn`: green `#4CAF50` — base button style
- `.rename-btn`: blue `#0288d1`
- `.check-btn`: purple `#7b1fa2`
- `.stop-btn`: red `#c62828`
- `.proceed-btn`: green `#2e7d32`
- `.editname-btn`: orange `#e65100`
- `#outnameEdit`: dark input box, 420px wide, hidden by default
- `#executionOutput`: dark monospace terminal output area, max-height 400px, scrollable
- `#topWarning`: orange warning banner, hidden by default
- `#dragSelectBox`: fixed position, blue border `#64b5f6`, semi-transparent fill, `pointer-events:none`, hidden by default
- `#csvActions`: flex row, hidden by default

### 6b. Header layout
Left side: "Select/Deselect All" button + `<h1>` title  
Right side: button group —
- Show Selected
- Create CBZ
- Rename
- "Check subfolders 4CBZing" ← only shown if `num_dirs > 0`

Hidden input `#currentAbsPath` with absolute path value.

### 6c. Table columns
`[checkbox] | Name | Items | Size | Modified`

- Sort: directories first, then files, both alphabetically (case-insensitive)
- Parent directory link `../` shown if not at root
- Directories: green class, `onclick="saveFolderScroll(name)"`, item count with tooltip `"N file(s), M folder(s)"`
- Files: size auto-scaled (B/KB/MB/GB)
- Each row has sanitized `id="row-{name}"` for scroll targeting
- Checkboxes: class `item-chk`, `data-isdir="true|false"`, `onchange="updateSelectedFiles()"`

### 6d. Below the table
```html
<div id="executionOutput">
  <h3>Terminal Output</h3>
  <div id="outputContent"></div>
  <div id="cbzConfirm">   <!-- hidden by default, flex when shown -->
    <button id="stopCBZBtn" class="stop-btn">✖ Stop!</button>
    <button class="proceed-btn">✔ Proceed now</button>
    <button class="editname-btn">✎ Rename</button>
    <input id="outnameEdit" type="text">
  </div>
  <div id="csvActions">   <!-- hidden by default -->
    <button>⬇ Download CSV</button>
    <button>📊 View in Browser</button>
  </div>
</div>
```

---

## 7. JavaScript

### 7a. State variables
```js
let selectedFiles = new Set();
let lastCsvPath = null;
let lastViewUrl = null;
let pendingCBZParams = null;
let cbzCountdownTimer = null;
let cbzCountdownInterval = null;
const CBZ_COUNTDOWN_SECS = 4;
```

### 7b. `isVolume(name)`
Regex: `/\b(?:v|vol|book|t)\.?\s*\d+|TPB|Omnibus|Collection|Graphic\s*Novel|GN|HC|Scanlation|Complete/i`

### 7c. `updateSelectedFiles()`
- Clear `selectedFiles`
- For each checked `.item-chk`: if `isVolume()` → uncheck and count as skipped; else add to set
- Show warning banner if any skipped

### 7d. `getSelectedFiles()`
- Call `updateSelectedFiles()`
- Return `Array.from(selectedFiles)`
- **Fallback**: if empty, return all non-volume filenames from DOM (checked or not)

### 7e. `toggleSelectAll()`
- Filter to only `data-isdir="false"` checkboxes
- If **any** checked → uncheck all; else check all
- Call `updateSelectedFiles()`

### 7f. `parseFilename(filename)`
Mirror of Python `parse_filename`. Returns `{series, subtitle, year}`.  
Supports both `Series 001` and `Series (001)` issue number formats (1–3 digit numbers in parentheses, distinct from 4-digit year tags).

### 7g. `getNextVolumeNumber(series)`
- Escape regex special chars in `series`
- Build pattern: `/^{series}.*\bv(\d+)\b.*\.cbz$/i`
- Scan all `.item-chk` values in DOM
- Return `maxFound + 1` (returns 1 if none found)

### 7h. `buildOutname(parsed)`
- Call `getNextVolumeNumber(parsed.series)` → format as `v01`, `v02` etc (zero-padded to 2 digits)
- Format: `"{series} {vol}"` + optional `" - {subtitle}"` + optional `" ({year})"`

### 7i. `getGroupName(f)`
Returns `parseFilename(f).series`

### 7j. `generateCBZParams(files)`
- Requires `files.length > 1`
- Detect series groups: if `> 1` group → return `{warning: true, groups: [...]}`
- Else return `{outname: buildOutname(parseFilename(files[0]))}`

### 7k. `showSelected()`
Alert with selected filenames + proposed outname.

### 7l. `promptRename()`
For folder/file rename (not CBZ outname). Requires exactly 1 selected item.  
`prompt()` dialog → POST `action:"rename"` → reload on success.

### 7m. `toggleRenameBox()`
Reveals/hides `#outnameEdit`.  
**When opening**: `clearTimeout(cbzCountdownTimer)` + `clearInterval(cbzCountdownInterval)` — stops auto-proceed countdown so user can edit freely. Reset stop button label to `"✖ Stop!"`.

### 7n. `prepareCreateCBZ()`
1. Get selected files, require ≥ 2
2. If `files.length > 6`: `confirm("You selected X files to CBZ. Are you sure?")` — abort if cancelled
3. Check groups — show warning if mixed series
4. Store `pendingCBZParams = {absPath, files, outname}`
5. Pre-fill `#outnameEdit` with proposed outname (hidden)
6. Show output box with file list display
7. Show `#cbzConfirm` buttons
8. Start countdown: update stop button label every second `"✖ Stop! (N)"`
9. `setTimeout(proceedCBZ, CBZ_COUNTDOWN_SECS * 1000)`

### 7o. `stopCBZ()`
- `clearTimeout` + `clearInterval`
- Hide output box and confirm buttons
- Clear `pendingCBZParams`

### 7p. `proceedCBZ()`
- `clearTimeout` + `clearInterval`
- If `#outnameEdit` is visible and non-empty: override `pendingCBZParams.outname`
- Hide confirm buttons and edit box
- Append `"\nRunning...\n"` to output
- POST `action:"create_cbz_direct"` with `{abs_path, files, outname}`
- On success: show log, start 10-second countdown to `location.reload()`
  - Countdown updates last line of output each second: `"--- Refreshing in N seconds... ---"`
- On error: show error, do not reload

### 7q. `checkSubfolders4CBZ()`
POST `action:"check_subfolders"`.  
On success: show summary in output, store `lastCsvPath`/`lastViewUrl`, show `#csvActions` buttons.

### 7r. `openCSVDownload()` / `openCSVViewer()`
`window.open(lastCsvPath/_lastViewUrl, '_blank')`

### 7s. Scroll restoration (`pageshow` event)
- On page show: check `sessionStorage` for `"scrollTarget:{pathname}"`
- If found: find matching row, smooth scroll to it, flash yellow highlight for 2 seconds
- Row matching: strip icon prefix and trailing `/` from link text

### 7t. Rubber-band drag selection (IIFE)
Implemented as immediately-invoked function expression to avoid polluting global scope.

**State**: `dragging`, `startX/Y`, `baseState` (Map of checkbox → bool at drag start)

**`mousedown`**:
- Only left-click (`e.button === 0`)
- Ignore if target is `input`, `a`, `button`, `th`
- Must be inside a `<tr>`
- Snapshot all `.item-chk` checked states into `baseState`
- Show `#dragSelectBox` at click position, size 0
- `e.preventDefault()`

**`mousemove`**:
- Update `#dragSelectBox` position and size
- Call `updateSelection(startX, startY, curX, curY)`
- Auto-scroll: if cursor within 40px of viewport top/bottom, `window.scrollBy(0, ±12)`

**`mouseup`**:
- Finalise selection
- Hide `#dragSelectBox`

**`mouseleave`**:
- Cancel drag, hide box

**`updateSelection(x1,y1,x2,y2)`**:
- Compute selection rect (min/max of start and current)
- For each `<tr>` with `.item-chk`: use `getBoundingClientRect()` to test overlap
- If overlap: check the checkbox; else restore from `baseState`
- Call `updateSelectedFiles()`

---

## 8. Behaviour notes

- Volume detection regex excludes from selection and CBZ creation: v1/v01/vol1, TPB, Omnibus, HC, GN, Collection, Graphic Novel, Scanlation, Complete
- `getNextVolumeNumber` scans only `.cbz` files (already-created volumes) in the current folder DOM listing to suggest the next volume number
- CBZ creation deletes source files only on **success** — never on failure
- The rename button (✎) in the CBZ confirm bar edits only the output filename, not the file list or process
- `makecbz.py` is **not used** by this script — CBZ creation is handled natively via `unrar`/`unzip`/`zip`
- Thread-safety: `subprocess.run(..., cwd=abs_path)` used instead of `os.chdir()`

---

## 9. System requirements

- Python 3.10+ (uses `list[str]` type hints in function signatures)
- `unrar` — for `.cbr` / RAR5 archives
- `unzip` — for `.cbz` / ZIP archives  
- `zip` (Info-ZIP) — for creating the output CBZ
- Linux filesystem (paths use `os.sep`, tested on Kubuntu/Debian 12)
