# Comic Archive Browser — Product Requirements
## action_explorer — Feature & Requirements Document

**Prepared by:** Business Analyst / Senior Developer  
**Status:** Current as of v11  
**Platform:** Linux desktop (Kubuntu/Debian), Firefox browser  

---

## 1. Purpose & Context

The user manages a large personal comic book collection stored as `.cbr` and `.cbz` archive files, organised in a folder hierarchy on a local Linux machine.

The primary pain point is **batch conversion**: individual issue files (e.g. 6 `.cbr` files representing issues 1–6 of a series) need to be merged into a single `.cbz` volume archive. Existing tools (`makecbz.py`) work but require terminal use and are prone to errors when many files exist in the same folder (glob patterns match unintended files).

A secondary need is **browsing and housekeeping**: navigating the folder structure, renaming files/folders, and auditing which series are ready to be merged.

The solution is a **self-contained Python web server** that serves a browser UI, accessible at `http://localhost:8123/`. No external web framework, no database, no installation beyond standard Linux tools.

---

## 2. User Roles

Single user (personal tool). No authentication required. No multi-user considerations.

---

## 3. Functional Requirements

### 3.1 Directory Browsing

| ID | Requirement |
|----|-------------|
| BR-01 | The server must serve any directory passed as a command-line argument, defaulting to the current directory |
| BR-02 | The directory listing must display: file/folder name, item count (for folders), file size (auto-scaled), last modified date |
| BR-03 | Folders must be sorted before files; both groups sorted alphabetically case-insensitively |
| BR-04 | Clicking a folder navigates into it; clicking a file serves/downloads it |
| BR-05 | A parent directory (`../`) link must be shown on all pages except the root |
| BR-06 | Folder item counts must show a tooltip with separate file and subfolder counts on hover |

### 3.2 File Selection

| ID | Requirement |
|----|-------------|
| SEL-01 | Each row must have a checkbox for selection |
| SEL-02 | A "Select/Deselect All" button must toggle all **file** checkboxes (not folders) — if any are checked it deselects all; if none are checked it selects all |
| SEL-03 | Selecting a file that matches the volume pattern must automatically deselect it and show a warning banner explaining why |
| SEL-04 | Volume pattern must detect: v1/v01/vol1, TPB, Omnibus, Collection, Graphic Novel, GN, HC, Scanlation, Complete |
| SEL-05 | If no files are explicitly checked when an action is triggered, all eligible non-volume files in the folder are treated as selected (implicit selection fallback) |
| SEL-06 | Rubber-band drag selection: clicking and dragging on the table background must draw a selection rectangle and check all rows it overlaps |
| SEL-07 | Drag selection must not activate when clicking on checkboxes, links, or buttons |
| SEL-08 | Drag selection must auto-scroll the page when the cursor approaches the viewport top or bottom edge |
| SEL-09 | Drag selection must preserve previously checked items outside the drag rectangle |

### 3.3 File & Folder Rename

| ID | Requirement |
|----|-------------|
| REN-01 | A "Rename" button must rename the single selected item (file or folder) |
| REN-02 | Exactly one item must be selected; if zero or more than one are selected, show an error alert |
| REN-03 | A native browser prompt pre-filled with the current name must be shown |
| REN-04 | The page must reload automatically after a successful rename |
| REN-05 | Rename errors (permissions, etc.) must be reported to the user |

### 3.4 CBZ Creation

| ID | Requirement |
|----|-------------|
| CBZ-01 | A "Create CBZ" button must merge the selected comic files into a single `.cbz` archive |
| CBZ-02 | At least 2 files must be selected; if fewer, show an error alert |
| CBZ-03 | If more than 6 files are selected, a confirmation dialog must ask the user to confirm before proceeding |
| CBZ-04 | If selected files belong to more than one detected series, show a warning and block creation |
| CBZ-05 | The proposed output filename must be derived from the first selected file: series name + next available volume number + subtitle (if present) + year (if present) |
| CBZ-06 | The volume number must be auto-detected by scanning existing `.cbz` files in the current folder — if `v01` and `v02` exist, suggest `v03` |
| CBZ-07 | Volume number must be zero-padded to 2 digits (v01, v02 … v10, v11) |
| CBZ-08 | Output filename format: `{Series} {vNN} - {Subtitle} ({Year})` — subtitle and year are optional |
| CBZ-09 | After clicking Create CBZ, the proposed output name and file list must be shown before execution begins |
| CBZ-10 | A countdown of 4 seconds must begin automatically; if not interrupted the operation proceeds |
| CBZ-11 | A "✖ Stop!" button must cancel the operation at any point before execution starts; the countdown remaining seconds must be shown on the button |
| CBZ-12 | A "✔ Proceed now" button must execute immediately without waiting for the countdown |
| CBZ-13 | A "✎ Rename" button must reveal an editable text field pre-filled with the proposed output name |
| CBZ-14 | Clicking Rename must immediately cancel the countdown — the user must click Proceed manually after editing |
| CBZ-15 | If the Rename field is visible and non-empty when Proceed is clicked, its value must be used as the output name |

### 3.5 CBZ Creation — Technical Process

| ID | Requirement |
|----|-------------|
| CBZ-T01 | Only the explicitly selected files must be processed — no glob patterns |
| CBZ-T02 | A temporary working folder named after the output file must be created in the current directory |
| CBZ-T03 | Each source file must be extracted into its own named subfolder within the working folder, preserving alphabetical order for correct page sequencing |
| CBZ-T04 | `.cbr` files must be extracted using `unrar` (supports RAR5) |
| CBZ-T05 | `.cbz` files must be extracted using `unzip` |
| CBZ-T06 | The working folder must be zipped using `zip -r` to produce the final `.cbz` |
| CBZ-T07 | The resulting `.cbz` must be moved from the working folder to the original folder |
| CBZ-T08 | Source files must be deleted after successful CBZ creation only — never on failure |
| CBZ-T09 | The working folder must be deleted after successful completion |
| CBZ-T10 | On failure at any step: log the error, attempt cleanup of the working folder, do not delete source files |

### 3.6 Execution Output

| ID | Requirement |
|----|-------------|
| OUT-01 | A terminal-style output panel must be shown during and after CBZ creation |
| OUT-02 | Output must be verbose and structured with step markers (`[1/6]`, `[2/6]` etc.) |
| OUT-03 | Each action within a step must be prefixed: `✔` for success, `✖` for failure, `·` for informational |
| OUT-04 | After successful completion, the output must remain visible for 10 seconds before the page auto-reloads |
| OUT-05 | A live countdown must be shown in the output panel during the 10-second delay |
| OUT-06 | On failure, the output must remain visible indefinitely (no auto-reload) |
| OUT-07 | The output panel must auto-scroll to the bottom as new lines appear |

### 3.7 Subfolder CBZ Audit ("Check subfolders 4CBZing")

| ID | Requirement |
|----|-------------|
| AUD-01 | A "Check subfolders 4CBZing" button must appear in the header only when the current folder contains at least one subfolder |
| AUD-02 | Clicking it must scan subfolders up to 2 levels deep |
| AUD-03 | For each subfolder, comic files must be grouped by detected series name |
| AUD-04 | Volume files (matching the volume pattern) must be excluded from grouping and counted separately |
| AUD-05 | Each group must be assigned a status: `ready` (≥2 files, no CBZ exists), `cbz_exists`, `single_file`, `no_comics`, `deeper_only` |
| AUD-06 | Folders at depth 2 that contain further subfolders must be flagged with `has_deeper_subfolders = true` |
| AUD-07 | Results must be written to a CSV file named `{current_folder_name}_checked.csv` in the current directory |
| AUD-08 | CSV columns: `path`, `series`, `file_count`, `volumes_skipped`, `status`, `proposed_outname`, `has_deeper_subfolders`, `files` |
| AUD-09 | A summary of counts per status must be shown in the output panel after scanning |
| AUD-10 | Two buttons must appear after scanning: "⬇ Download CSV" and "📊 View in Browser" |

### 3.8 CSV Viewer

| ID | Requirement |
|----|-------------|
| CSV-01 | The CSV must be viewable as a styled HTML page at `/view_csv?file=<path>` |
| CSV-02 | The viewer must use the same dark theme as the main browser |
| CSV-03 | Summary pill badges must show counts per status at the top of the page |
| CSV-04 | Filter buttons must allow showing only rows of a specific status |
| CSV-05 | All columns must be sortable by clicking the column header (toggle asc/desc); numeric columns must sort numerically |
| CSV-06 | Status column must show a colour-coded badge |
| CSV-07 | Path column must be a clickable link that opens the folder in the file browser in a new tab |
| CSV-08 | Series column must show the series name plus a smaller grey link below it pointing to `{path}/{series}/` — Ctrl+click opens that subfolder in a new tab |
| CSV-09 | A `← Back` link must return to the previous page |

---

## 4. Filename Parsing Requirements

| ID | Requirement |
|----|-------------|
| FP-01 | The parser must extract: series name, subtitle, year from standard comic naming conventions |
| FP-02 | Standard format supported: `{Series} {issue} (of {total}) - {Subtitle} ({Year}) ({Tag})...ext` |
| FP-03 | Issue number formats supported: `01`, `#01`, `01 (of 05)`, `#01 (of 05)` |
| FP-04 | Publisher/quality tags in parentheses (e.g. `(Digital)`, `(Zone-Empire)`) must be stripped from subtitle |
| FP-05 | Year must be a 4-digit number in parentheses e.g. `(2025)` |
| FP-06 | Parser must be implemented identically in both Python (server) and JavaScript (client) |

---

## 5. Scroll Restoration

| ID | Requirement |
|----|-------------|
| SCR-01 | When navigating into a subfolder and pressing Back, the parent listing must scroll to the folder that was clicked |
| SCR-02 | The restored row must be highlighted with a yellow flash animation for 2 seconds |
| SCR-03 | Scroll position must be stored in `sessionStorage` keyed by pathname |

---

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | No external Python packages — stdlib only |
| NFR-02 | System dependencies: `unrar`, `unzip`, `zip` |
| NFR-03 | Python 3.10+ required |
| NFR-04 | Server must handle `KeyboardInterrupt` gracefully and call `server_close()` |
| NFR-05 | Subprocess calls must use `cwd=` parameter, never `os.chdir()`, to avoid thread-safety issues |
| NFR-06 | The entire application must be a single `.py` file — no templates, no static assets |
| NFR-07 | The UI must be usable in Firefox on Linux; no browser-specific APIs beyond standard DOM |
| NFR-08 | Dark theme throughout — background `#121212`, text `#e0e0e0`, no white pages |

---

## 7. Out of Scope

- Multi-user access or authentication
- Editing image content inside archives
- Uploading files via the browser
- Sorting/renaming pages within a CBZ
- Integration with any comic reading application
- Windows or macOS support (Linux only)
- Mobile/touch device support

---

## 8. Glossary

| Term | Definition |
|------|------------|
| CBZ | Comic Book ZIP — a ZIP archive containing image files, standard comic format |
| CBR | Comic Book RAR — a RAR archive containing image files |
| RAR5 | Newer RAR compression format; requires `unrar`, not supported by `p7zip` |
| Volume | A collected edition of multiple issues, identified by naming patterns like `v01`, `TPB`, `Omnibus` |
| Series | The title of a comic series, parsed from the filename before the issue number |
| Outname | The proposed output filename for a new CBZ (without extension) |
| Rubber-band selection | Click-and-drag selection rectangle, common in file managers |
| Implicit selection | When no checkboxes are ticked, all eligible files are treated as selected |
