"""
Script: action_explorer_v06.py
Version: v06
Description: A custom HTTP web server that provides an interactive directory listing.
Includes features to create CBZ archives and rename files/folders directly from the UI.
v06 adds "Check subfolders 4CBZing": scans up to 2 levels of subfolders, groups comic
files by series using the same parseFilename logic, and writes a CSV report.
CSV columns: path, series, file_count, volumes_skipped, status, proposed_outname,
             has_deeper_subfolders, files
Statuses: ready | single_file | cbz_exists | no_comics | deeper_only
"""

import os
import sys
import re
import csv
import io
import urllib.parse
import html
import datetime
import json
import subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer

COMIC_EXTS = {'.cbz', '.cbr', '.zip', '.rar'}
VOLUME_PATTERN = re.compile(
    r'\b(?:v|vol|book|t)\.?\s*\d+|TPB|Omnibus|Collection|Graphic\s*Novel|GN|HC|Scanlation|Complete',
    re.IGNORECASE
)


def is_volume(name: str) -> bool:
    return bool(VOLUME_PATTERN.search(name))


def parse_filename(filename: str) -> dict:
    """Mirror of the JS parseFilename function.
    Returns { series, subtitle, year } from a comic filename."""
    name = re.sub(r'\.(cbz|cbr|zip|rar)$', '', filename, flags=re.IGNORECASE)

    year_match = re.search(r'\((\d{4})\)', name)
    year = year_match.group(1) if year_match else None

    series_match = re.match(r'^(.*?)(?:\s+#?\d+(?:\s*\(of\s*\d+\))?)', name, re.IGNORECASE)
    series = series_match.group(1).strip() if series_match else name

    subtitle = None
    subtitle_match = re.search(r'#?\d+(?:\s*\(of\s*\d+\))?\s*-\s*(.+)', name, re.IGNORECASE)
    if subtitle_match:
        sub = subtitle_match.group(1)
        sub = re.sub(r'\(\d{4}\)', '', sub)
        sub = re.sub(r'\([^)]+\)', '', sub)
        sub = re.sub(r'\s+', ' ', sub).strip()
        subtitle = sub if sub else None

    return {'series': series, 'subtitle': subtitle, 'year': year}


def build_outname(parsed: dict) -> str:
    """Mirror of the JS buildOutname function."""
    out = parsed['series'] + ' v01'
    if parsed['subtitle']:
        out += ' - ' + parsed['subtitle']
    if parsed['year']:
        out += ' (' + parsed['year'] + ')'
    return out


def check_folder_for_cbz(folder_path: str) -> list[dict]:
    """Scan folder_path up to 2 levels deep.
    Returns a list of row dicts for the CSV report."""
    rows = []

    def scan(dirpath: str, depth: int):
        try:
            entries = os.listdir(dirpath)
        except OSError:
            return

        subdirs = [e for e in entries if os.path.isdir(os.path.join(dirpath, e))]
        comic_files = [
            e for e in entries
            if os.path.isfile(os.path.join(dirpath, e))
            and os.path.splitext(e)[1].lower() in COMIC_EXTS
        ]

        # Check for subfolders deeper than our scan limit
        has_deeper = False
        if depth == 2:
            has_deeper = len(subdirs) > 0

        # Group comic files by series
        groups: dict[str, list[str]] = {}
        volumes_skipped: list[str] = []
        for f in comic_files:
            if is_volume(f):
                volumes_skipped.append(f)
                continue
            series = parse_filename(f)['series']
            groups.setdefault(series, []).append(f)

        if not groups and not comic_files:
            # No comics at all at this level — only report if no subdirs to recurse into
            if depth == 2 or not subdirs:
                rows.append({
                    'path': dirpath,
                    'series': '',
                    'file_count': 0,
                    'volumes_skipped': len(volumes_skipped),
                    'status': 'no_comics',
                    'proposed_outname': '',
                    'has_deeper_subfolders': has_deeper,
                    'files': ''
                })
        else:
            for series, files in groups.items():
                files_sorted = sorted(files)
                parsed = parse_filename(files_sorted[0])
                proposed = build_outname(parsed)

                # Determine status
                existing_cbz = [
                    e for e in entries
                    if os.path.isfile(os.path.join(dirpath, e))
                    and os.path.splitext(e)[1].lower() == '.cbz'
                    and series.lower() in e.lower()
                ]
                if existing_cbz:
                    status = 'cbz_exists'
                elif len(files) >= 2:
                    status = 'ready'
                else:
                    status = 'single_file'

                rows.append({
                    'path': dirpath,
                    'series': series,
                    'file_count': len(files),
                    'volumes_skipped': len(volumes_skipped),
                    'status': status,
                    'proposed_outname': proposed,
                    'has_deeper_subfolders': has_deeper,
                    'files': ' | '.join(files_sorted)
                })

            # Also report volume-only folders with no issues
            if not groups and volumes_skipped:
                rows.append({
                    'path': dirpath,
                    'series': '',
                    'file_count': 0,
                    'volumes_skipped': len(volumes_skipped),
                    'status': 'no_comics',
                    'proposed_outname': '',
                    'has_deeper_subfolders': has_deeper,
                    'files': ''
                })

        # Recurse into subdirs up to depth 2
        if depth < 2:
            for sub in sorted(subdirs):
                scan(os.path.join(dirpath, sub), depth + 1)
        elif subdirs:
            # At max depth, note that deeper subfolders exist but aren't scanned
            # (already captured in has_deeper above per-row; add a sentinel row if
            # the folder had *only* subdirs and no comics to report)
            if not groups and not comic_files:
                rows.append({
                    'path': dirpath,
                    'series': '',
                    'file_count': 0,
                    'volumes_skipped': 0,
                    'status': 'deeper_only',
                    'proposed_outname': '',
                    'has_deeper_subfolders': True,
                    'files': ''
                })

    # Start scanning immediate subfolders of the root (depth=1)
    try:
        top_entries = os.listdir(folder_path)
    except OSError:
        return rows

    top_subdirs = sorted(e for e in top_entries if os.path.isdir(os.path.join(folder_path, e)))
    for sub in top_subdirs:
        scan(os.path.join(folder_path, sub), depth=1)

    return rows


class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        action = data.get('action')
        abs_path = data.get('abs_path')

        # --- Handle Rename Action ---
        if action == 'rename':
            old_name = data.get('old_name')
            new_name = data.get('new_name')
            try:
                os.rename(os.path.join(abs_path, old_name), os.path.join(abs_path, new_name))
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
            return

        # --- Handle Check Subfolders Action ---
        if action == 'check_subfolders':
            try:
                rows = check_folder_for_cbz(abs_path)

                folder_name = os.path.basename(abs_path.rstrip('/\\')) or 'root'
                csv_filename = folder_name + '_checked.csv'
                csv_path = os.path.join(abs_path, csv_filename)

                fieldnames = ['path', 'series', 'file_count', 'volumes_skipped',
                              'status', 'proposed_outname', 'has_deeper_subfolders', 'files']

                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)

                total = len(rows)
                ready = sum(1 for r in rows if r['status'] == 'ready')
                exists = sum(1 for r in rows if r['status'] == 'cbz_exists')
                single = sum(1 for r in rows if r['status'] == 'single_file')
                no_comics = sum(1 for r in rows if r['status'] == 'no_comics')
                deeper = sum(1 for r in rows if r['status'] == 'deeper_only')

                summary = (
                    f"Scan complete — {total} group(s) found across subfolders.\n\n"
                    f"  ready        : {ready}  (2+ files, no existing CBZ)\n"
                    f"  cbz_exists   : {exists}  (CBZ already present)\n"
                    f"  single_file  : {single}  (only 1 issue found)\n"
                    f"  no_comics    : {no_comics}  (no comic files)\n"
                    f"  deeper_only  : {deeper}  (subfolders beyond scan depth)\n\n"
                    f"CSV saved to: {csv_path}"
                )

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'output': summary, 'csv_path': csv_path}).encode())

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
            return

        # --- Handle CBZ Creation Action ---
        pattern = data.get('pattern')
        outname = data.get('outname')

        try:
            cmd = ["python3", "/home/nesha/scripts/makecbz.py", pattern, outname]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=abs_path)
            output = result.stdout + result.stderr

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'output': output}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def list_directory(self, path):
        try:
            list_dir = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None

        list_dir.sort(key=lambda a: (not os.path.isdir(os.path.join(path, a)), a.lower()))
        displaypath = html.escape(urllib.parse.unquote(self.path))
        enc = sys.getfilesystemencoding()
        title = f'Directory listing for {displaypath}'

        r: list[str] = []

        r.append('<!DOCTYPE HTML>\n<html>\n<head>')
        r.append(f'<meta charset="{enc}">')
        r.append(f'<title>{title}</title>')
        r.append('<style>')
        r.append('body { font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 2rem; background: #121212; color: #e0e0e0; }')
        r.append('h1 { color: #ffffff; margin: 0; }')
        r.append('table { width: 100%; border-collapse: collapse; background: #1e1e1e; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }')
        r.append('th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #333; }')
        r.append('th { background: #2c2c2c; font-weight: 600; color: #ffffff; }')
        r.append('tr:last-child td { border-bottom: none; }')
        r.append('tr:hover { background: #2a2a2a; }')
        r.append('a { color: #64b5f6; text-decoration: none; font-weight: 500; display: block; }')
        r.append('a:hover { color: #90caf9; text-decoration: underline; }')
        r.append('.dir { color: #81c784; font-weight: bold; }')
        r.append('.dir:hover { color: #a5d6a7; }')
        r.append('.count-btn { background-color: #4CAF50; border: none; color: white; padding: 10px 20px; text-align: center; cursor: pointer; border-radius: 4px; font-size: 16px; }')
        r.append('.count-btn:hover { background-color: #45a049; }')
        r.append('.rename-btn { background-color: #0288d1; }')
        r.append('.rename-btn:hover { background-color: #039be5; }')
        r.append('.check-btn { background-color: #7b1fa2; }')
        r.append('.check-btn:hover { background-color: #9c27b0; }')
        r.append('.header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }')
        r.append('.button-group { display: flex; gap: 10px; }')
        r.append('#executionOutput { display: none; margin-top: 30px; background: #1e1e1e; color: #d4d4d4; padding: 15px; font-family: "Courier New", Courier, monospace; border-radius: 5px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; box-shadow: inset 0 0 10px #000; border: 1px solid #333; }')
        r.append('#executionOutput h3 { color: #569cd6; margin-top: 0; font-size: 1em; border-bottom: 1px solid #333; padding-bottom: 5px; }')
        r.append('#topWarning { display: none; background: #ff9800; color: #000; padding: 10px; margin-bottom: 20px; border-radius: 4px; font-weight: bold; text-align: center; }')
        r.append('</style>\n</head>\n<body>')

        r.append('<div id="topWarning"></div>')

        abs_path = os.path.abspath(path)

        # Count dirs to decide whether to show the Check button
        num_dirs = sum(1 for e in list_dir if os.path.isdir(os.path.join(path, e)))

        r.append('<div class="header-container">')
        r.append('<div style="display: flex; align-items: center; gap: 15px;">')
        r.append('<button class="count-btn" onclick="toggleSelectAll()">Select/Deselect All</button>')
        r.append(f'<h1>{title}</h1>')
        r.append('</div>')
        r.append('<div class="button-group">')
        r.append(f'<input type="hidden" id="currentAbsPath" value="{html.escape(abs_path)}">')
        r.append('<button class="count-btn" onclick="showSelected()">Show Selected</button>')
        r.append('<button class="count-btn" onclick="prepareCreateCBZ()">Create CBZ</button>')
        r.append('<button class="count-btn rename-btn" onclick="promptRename()">Rename</button>')
        if num_dirs > 0:
            r.append('<button class="count-btn check-btn" onclick="checkSubfolders4CBZ()">Check subfolders 4CBZing</button>')
        r.append('</div>')
        r.append('</div>')

        r.append('<table>')
        r.append('<tr><th style="width: 30px;"></th><th>Name</th><th>Items</th><th>Size</th><th>Modified</th></tr>')

        if self.path != '/':
            r.append('<tr><td></td><td><a href="../" class="dir">📁 ../ (Parent Directory)</a></td><td>-</td><td>-</td><td>-</td></tr>')

        for name in list_dir:
            fullname = os.path.join(path, name)
            is_dir = os.path.isdir(fullname)
            displayname = ("📁 " if is_dir else "📄 ") + name + ("/" if is_dir else "")
            linkname = urllib.parse.quote(name + ("/" if is_dir else ""), errors='surrogatepass')

            try:
                stat = os.stat(fullname)
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                if is_dir:
                    size_str = '-'
                    try:
                        sub_entries = os.listdir(fullname)
                        sub_files = sum(1 for e in sub_entries if os.path.isfile(os.path.join(fullname, e)))
                        sub_dirs = sum(1 for e in sub_entries if os.path.isdir(os.path.join(fullname, e)))
                        items_str = str(sub_files + sub_dirs)
                        items_title = f'{sub_files} file(s), {sub_dirs} folder(s)'
                    except OSError:
                        items_str = '?'
                        items_title = 'Cannot read folder'
                else:
                    size = stat.st_size
                    items_str = '-'
                    items_title = ''
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 ** 2:
                        size_str = f"{size / 1024:.1f} KB"
                    elif size < 1024 ** 3:
                        size_str = f"{size / 1024 ** 2:.1f} MB"
                    else:
                        size_str = f"{size / 1024 ** 3:.1f} GB"
            except OSError:
                size_str = items_str = items_title = mtime = '-'

            row_id = html.escape(name).replace(' ', '_').replace('(', '').replace(')', '').replace('.', '_').replace("'", '').replace('&', '').replace('+', '').replace(',', '')
            chk_box = f'<input type="checkbox" class="item-chk" value="{html.escape(name)}" data-isdir="{"true" if is_dir else "false"}" onchange="updateSelectedFiles()">'
            a_class = 'class="dir"' if is_dir else ''
            onclick = f'onclick="saveFolderScroll(\'{html.escape(name)}\')"' if is_dir else ''

            r.append(
                f'<tr id="row-{row_id}">'
                f'<td>{chk_box}</td>'
                f'<td><a href="{linkname}" {a_class} {onclick}>{html.escape(displayname)}</a></td>'
                f'<td title="{html.escape(items_title)}" style="color:#888;font-size:0.9em">{items_str}</td>'
                f'<td>{size_str}</td>'
                f'<td>{mtime}</td>'
                f'</tr>'
            )

        r.append('</table>')
        r.append('<div id="executionOutput"><h3>Terminal Output</h3><div id="outputContent"></div></div>')

        # --- JavaScript ---
        r.append('<script>')

        r.append('''
let selectedFiles = new Set();

function isVolume(name) {
  const skipPattern = /\\b(?:v|vol|book|t)\\.?\\s*\\d+|TPB|Omnibus|Collection|Graphic\\s*Novel|GN|HC|Scanlation|Complete/i;
  return skipPattern.test(name);
}

function hideWarning() {
  document.getElementById("topWarning").style.display = "none";
}

function showWarning(msg) {
  let w = document.getElementById("topWarning");
  w.innerText = msg;
  w.style.display = "block";
}

function updateSelectedFiles() {
  hideWarning();
  selectedFiles.clear();
  let skipped = 0;
  document.querySelectorAll(".item-chk").forEach(chk => {
    if (chk.checked) {
      if (isVolume(chk.value)) {
        chk.checked = false;
        skipped++;
      } else {
        selectedFiles.add(chk.value);
      }
    }
  });
  if (skipped > 0) {
    showWarning(skipped + " item(s) skipped — Volume/Collected editions are excluded from batch actions.");
  }
}

function getSelectedFiles() {
  updateSelectedFiles();
  let files = Array.from(selectedFiles);
  if (files.length === 0) {
    document.querySelectorAll(".item-chk").forEach(chk => {
      if (!isVolume(chk.value)) {
        files.push(chk.value);
      }
    });
  }
  return files;
}

function toggleSelectAll() {
  const chks = document.querySelectorAll(".item-chk");
  const allChecked = Array.from(chks).every(c => c.checked);
  chks.forEach(c => { c.checked = !allChecked; });
  updateSelectedFiles();
}

function saveFolderScroll(name) {
  sessionStorage.setItem("scrollTarget:" + window.location.pathname, name);
}

window.addEventListener("pageshow", function () {
  let key = "scrollTarget:" + window.location.pathname;
  let target = sessionStorage.getItem(key);
  if (!target) return;
  sessionStorage.removeItem(key);
  document.querySelectorAll("tr").forEach(row => {
    let link = row.querySelector("a");
    if (link && link.textContent.trim().replace(/^[\\S]+\\s*/, "").replace(/\\/$/, "") === target) {
      setTimeout(() => {
        row.scrollIntoView({ behavior: "smooth", block: "center" });
        row.style.transition = "background 0.5s";
        row.style.background = "#fffbcc";
        setTimeout(() => { row.style.background = ""; }, 2000);
      }, 50);
    }
  });
});

// --- Filename parsing ---

function parseFilename(filename) {
  let name = filename.replace(/\\.(cbz|cbr|zip|rar)$/i, "");
  let yearMatch = name.match(/\\((\\d{4})\\)/);
  let year = yearMatch ? yearMatch[1] : null;
  let seriesMatch = name.match(/^(.*?)(?:\\s+#?\\d+(?:\\s*\\(of\\s*\\d+\\))?)/i);
  let series = seriesMatch ? seriesMatch[1].trim() : name;
  let subtitleMatch = name.match(/#?\\d+(?:\\s*\\(of\\s*\\d+\\))?\\s*-\\s*(.+)/i);
  let subtitle = null;
  if (subtitleMatch) {
    subtitle = subtitleMatch[1]
      .replace(/\\(\\d{4}\\)/g, '')
      .replace(/\\([^)]+\\)/g, '')
      .replace(/\\s+/g, ' ')
      .trim();
    if (!subtitle) subtitle = null;
  }
  return { series, subtitle, year };
}

function buildOutname(parsed) {
  let out = parsed.series + " v01";
  if (parsed.subtitle) out += " - " + parsed.subtitle;
  if (parsed.year) out += " (" + parsed.year + ")";
  return out;
}

function getGroupName(filename) {
  return parseFilename(filename).series;
}

function generateCBZParams(files) {
  if (files.length <= 1) return null;
  let groups = new Set(files.map(f => getGroupName(f)));
  if (groups.size > 1) {
    return { warning: true, groups: Array.from(groups) };
  }
  let parsed = parseFilename(files[0]);
  return {
    pattern: parsed.series + "*.*",
    outname: buildOutname(parsed)
  };
}

function showSelected() {
  hideWarning();
  let files = getSelectedFiles();
  if (files.length === 0) { alert("No files available!"); return; }
  let msg = "Selected files:\\n\\n" + files.join("\\n");
  let cmdInfo = generateCBZParams(files);
  if (cmdInfo && !cmdInfo.warning) {
    msg += "\\n\\nProposed command:\\npython3 \\"/home/nesha/scripts/makecbz.py\\" \\"" + cmdInfo.pattern + "\\" \\"" + cmdInfo.outname + "\\"";
  }
  alert(msg);
}

function promptRename() {
  let files = getSelectedFiles();
  if (files.length !== 1) { alert("Please select exactly one item to rename."); return; }
  let oldName = files[0];
  let newName = prompt("Enter new name:", oldName);
  if (newName && newName !== oldName) {
    fetch("/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "rename",
        abs_path: document.getElementById("currentAbsPath").value,
        old_name: oldName,
        new_name: newName
      })
    })
    .then(res => res.json())
    .then(data => { if (data.error) alert("Rename failed: " + data.error); else location.reload(); })
    .catch(err => alert("Connection error: " + err));
  }
}

function prepareCreateCBZ() {
  hideWarning();
  let files = getSelectedFiles();
  if (files.length < 2) { alert("Select at least 2 files to create a merged CBZ."); return; }

  let cmdInfo = generateCBZParams(files);
  if (cmdInfo.warning) {
    showWarning("WARNING: More than one file group detected: " + cmdInfo.groups.map(s => "\\"" + s + "\\"").join(", ") + " — deselect files from the wrong series before continuing.");
    return;
  }

  let absPath = document.getElementById("currentAbsPath").value;
  let outputDiv = document.getElementById("executionOutput");
  let contentDiv = document.getElementById("outputContent");

  let fullCmd = "$ cd \\"" + absPath + "\\"\\n$ python3 \\"/home/nesha/scripts/makecbz.py\\" \\"" + cmdInfo.pattern + "\\" \\"" + cmdInfo.outname + "\\"";

  outputDiv.style.display = "block";
  contentDiv.innerText = fullCmd + "\\n\\n";
  outputDiv.scrollIntoView({ behavior: "smooth" });

  fetch("/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      abs_path: absPath,
      pattern: cmdInfo.pattern,
      outname: cmdInfo.outname
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      contentDiv.innerText += "ERROR: " + data.error;
    } else {
      contentDiv.innerText += data.output;
      contentDiv.innerText += "\\n\\n--- Done. Refreshing in 2.5 seconds... ---";
      setTimeout(() => { location.reload(); }, 2500);
    }
  })
  .catch(err => {
    contentDiv.innerText += "CONNECTION ERROR: " + err;
  });
}

function checkSubfolders4CBZ() {
  hideWarning();
  let absPath = document.getElementById("currentAbsPath").value;
  let outputDiv = document.getElementById("executionOutput");
  let contentDiv = document.getElementById("outputContent");

  outputDiv.style.display = "block";
  contentDiv.innerText = "Scanning subfolders (up to 2 levels deep)...\\n";
  outputDiv.scrollIntoView({ behavior: "smooth" });

  fetch("/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "check_subfolders", abs_path: absPath })
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      contentDiv.innerText += "ERROR: " + data.error;
    } else {
      contentDiv.innerText += data.output;
    }
  })
  .catch(err => {
    contentDiv.innerText += "CONNECTION ERROR: " + err;
  });
}
''')

        r.append('</script></body></html>')

        encoded = '\n'.join(r).encode(enc, 'surrogateescape')
        self.send_response(200)
        self.send_header("Content-type", f"text/html; charset={enc}")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
        return None


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Serve a directory with a custom HTML index.")
    parser.add_argument("target_dir", nargs="?", default=".", help="Directory to serve (default: current directory)")
    args = parser.parse_args()

    try:
        os.chdir(args.target_dir)
    except Exception as e:
        print(f"Failed to chdir to {args.target_dir}: {e}")
        sys.exit(1)

    server_address = ('', 8123)
    httpd = HTTPServer(server_address, CustomHandler)
    print(f"Serving {args.target_dir} at http://localhost:8123/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()
