"""
Script: action_explorer_v05.py
Version: v05
Description: A custom HTTP web server that provides an interactive directory listing.
Includes features to create CBZ archives and rename files/folders directly from the UI.
v05 adds smart outname generation: extracts series, subtitle and year from filenames
to produce rich output names like "The Cold Witch - A Tale of the Shrouded College (2025) v01"
instead of the naive "The Cold Witch v01".
"""

import os
import sys
import urllib.parse
import html
import datetime
import json
import subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer


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

        # --- Handle CBZ Creation Action ---
        pattern = data.get('pattern')
        outname = data.get('outname')

        try:
            cmd = ["python3", "/home/nesha/scripts/makecbz.py", pattern, outname]
            # Use cwd= instead of os.chdir to avoid thread-safety issues
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
        r.append('.header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }')
        r.append('.button-group { display: flex; gap: 10px; }')
        r.append('.cmd-box { background: #eee; padding: 10px; font-family: monospace; overflow-x: auto; white-space: pre-wrap; margin-bottom: 20px; border-left: 5px solid #ccc; color: #333; }')
        r.append('#executionOutput { display: none; margin-top: 30px; background: #1e1e1e; color: #d4d4d4; padding: 15px; font-family: "Courier New", Courier, monospace; border-radius: 5px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; box-shadow: inset 0 0 10px #000; border: 1px solid #333; }')
        r.append('#executionOutput h3 { color: #569cd6; margin-top: 0; font-size: 1em; border-bottom: 1px solid #333; padding-bottom: 5px; }')
        r.append('#topWarning { display: none; background: #ff9800; color: #000; padding: 10px; margin-bottom: 20px; border-radius: 4px; font-weight: bold; text-align: center; }')
        r.append('</style>\n</head>\n<body>')

        r.append('<div id="topWarning"></div>')

        abs_path = os.path.abspath(path)

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

            # Sanitized row id for scroll targeting
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
  // Fallback: if nothing explicitly checked, use all eligible non-volume files
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

// --- Filename parsing (v05) ---

// Parse a comic filename into { series, subtitle, year }.
// Input:  "The Cold Witch 01 (of 05) - A Tale of the Shrouded College (2025) (Digital) (Zone-Empire).cbr"
// Output: { series: "The Cold Witch", subtitle: "A Tale of the Shrouded College", year: "2025" }
function parseFilename(filename) {
  let name = filename.replace(/\\.(cbz|cbr|zip|rar)$/i, "");

  // Extract year: first (YYYY) found
  let yearMatch = name.match(/\\((\\d{4})\\)/);
  let year = yearMatch ? yearMatch[1] : null;

  // Extract series: everything before the issue number block
  // Handles: "Title 01", "Title 01 (of 05)", "Title #01", "Title #01 (of 05)"
  let seriesMatch = name.match(/^(.*?)(?:\\s+#?\\d+(?:\\s*\\(of\\s*\\d+\\))?)/i);
  let series = seriesMatch ? seriesMatch[1].trim() : name;

  // Extract subtitle: text after " - " that follows the issue/parenthetical block
  // Matches the " - Subtitle..." portion after the issue number and optional (of N)
  let subtitleMatch = name.match(/#?\\d+(?:\\s*\\(of\\s*\\d+\\))?\\s*-\\s*(.+)/i);
  let subtitle = null;
  if (subtitleMatch) {
    subtitle = subtitleMatch[1]
      .replace(/\\(\\d{4}\\)/g, '')    // remove year tags: (2025)
      .replace(/\\([^)]+\\)/g, '')     // remove remaining tags: (Digital) (Zone-Empire)
      .replace(/\\s+/g, ' ')           // collapse any double spaces left behind
      .trim();
    if (!subtitle) subtitle = null;
  }

  return { series, subtitle, year };
}

// Build a rich output name from parsed components.
// "The Cold Witch" + "A Tale of the Shrouded College" + "2025" -> "The Cold Witch - A Tale of the Shrouded College (2025) v01"
function buildOutname(parsed) {
  let out = parsed.series + " v01";
  if (parsed.subtitle) out += " - " + parsed.subtitle;
  if (parsed.year) out += " (" + parsed.year + ")";
  return out;
}

// For grouping purposes, series name is enough
function getGroupName(filename) {
  return parseFilename(filename).series;
}

function generateCBZParams(files) {
  if (files.length <= 1) return null;
  let groups = new Set(files.map(f => getGroupName(f)));
  if (groups.size > 1) {
    return { warning: true, groups: Array.from(groups) };
  }
  // Use the first file to derive subtitle and year for the outname
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
