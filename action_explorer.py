"""
Script: action_explorer.py
Version: v03 (Updated with Type Hinting)
Description: A custom HTTP web server that provides an interactive directory listing. 
Includes features to create CBZ archives and rename files/folders directly from the UI.
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
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
            return

        # --- Handle CBZ Creation Action ---
        pattern = data.get('pattern')
        outname = data.get('outname')
        
        try:
            cwd = os.getcwd()
            os.chdir(abs_path)
            cmd = ["python3", "/home/nesha/scripts/makecbz.py", pattern, outname]
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout + result.stderr
            os.chdir(cwd)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'output': output}).encode())
            
        except Exception as e:
            self.send_response(500)
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
        
        # Updated declaration with type hint
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
        r.append('tr:hover { background: #2a2a2a; }')
        r.append('a { color: #64b5f6; text-decoration: none; font-weight: 500; display: block; }')
        r.append('.dir { color: #81c784; font-weight: bold; }')
        r.append('.count-btn { background-color: #4CAF50; border: none; color: white; padding: 10px 20px; text-align: center; cursor: pointer; border-radius: 4px; }')
        r.append('.rename-btn { background-color: #0288d1; }')
        r.append('.rename-btn:hover { background-color: #039be5; }')
        r.append('.header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }')
        r.append('.button-group { display: flex; gap: 10px; }')
        r.append('.modal { display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }')
        r.append('.modal-content { background-color: #1e1e1e; margin: 15% auto; padding: 20px; border: 1px solid #888; width: 50%; border-radius: 8px; color: white; text-align: center; }')
        r.append('.cmd-box { background: #eee; padding: 10px; font-family: monospace; overflow-x: auto; white-space: pre-wrap; margin-bottom: 20px; border-left: 5px solid #ccc; color: #333; }')
        r.append('#executionOutput { display: none; margin-top: 30px; background: #1e1e1e; color: #d4d4d4; padding: 15px; font-family: monospace; border-radius: 5px; border: 1px solid #333; }')
        r.append('#topWarning { display: none; background: #ff9800; color: #000; padding: 10px; margin-bottom: 20px; border-radius: 4px; font-weight: bold; text-align: center; }')
        r.append('</style>\n</head>\n<body>')
        r.append('<div id="topWarning">Some items were automatically deselected (Volume/Collected patterns detected).</div>')
        
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
                    sub_entries = os.listdir(fullname)
                    items_str = str(len(sub_entries))
                else:
                    size = stat.st_size
                    items_str = '-'
                    if size < 1024: size_str = f"{size} B"
                    elif size < 1024**2: size_str = f"{size/1024:.1f} KB"
                    elif size < 1024**3: size_str = f"{size/1024**2:.1f} MB"
                    else: size_str = f"{size/1024**3:.1f} GB"
            except OSError:
                size_str = items_str = mtime = '-'
            
            chk_box = f'<input type="checkbox" class="item-chk" value="{html.escape(name)}" data-isdir="{"true" if is_dir else "false"}" onchange="updateSelectedFiles()">'
            r.append(f'<tr><td>{chk_box}</td><td><a href="{linkname}" class="{"dir" if is_dir else ""}" onclick="saveFolderScroll(\'{html.escape(name)}\')">{html.escape(displayname)}</a></td><td>{items_str}</td><td>{size_str}</td><td>{mtime}</td></tr>')
            
        r.append('</table>')
        r.append('<div id="executionOutput"><h3>Terminal Output</h3><div id="outputContent"></div></div>')
        
        # --- Scripts ---
        r.append('<script>')
        r.append('let selectedFiles = new Set();')
        
        r.append('function isVolume(name) { const skipPattern = /\\b(?:v|vol|book|t)\\.?\\s*\\d+|TPB|Omnibus|Collection|Graphic\\s*Novel|GN|HC|Scanlation|Complete/i; return skipPattern.test(name); }')
        
        r.append('function updateSelectedFiles() {')
        r.append('  let skippedCount = 0;')
        r.append('  document.querySelectorAll(".item-chk").forEach(chk => {')
        r.append('    if(chk.checked) {')
        r.append('      if(isVolume(chk.value)) { chk.checked = false; skippedCount++; selectedFiles.delete(chk.value); }')
        r.append('      else { selectedFiles.add(chk.value); }')
        r.append('    } else { selectedFiles.delete(chk.value); }')
        r.append('  });')
        r.append('  let w = document.getElementById("topWarning");')
        r.append('  if(skippedCount > 0) { w.style.display = "block"; w.innerText = skippedCount + " item(s) skipped (Volume/Collected files are excluded from batch actions)."; }')
        r.append('  else { w.style.display = "none"; }')
        r.append('}')
        
        r.append('function getSelectedFiles() { updateSelectedFiles(); return Array.from(selectedFiles); }')
        
        r.append('function hideWarning() { let w = document.getElementById("topWarning"); if(w) w.style.display="none"; }')

        r.append('function showSelected() {')
        r.append('  hideWarning(); let files = getSelectedFiles();')
        r.append('  if (files.length === 0) { alert("No files available!"); return; }')
        r.append('  let msg = "Selected files:\\n\\n" + files.join("\\n");')
        r.append('  alert(msg);')
        r.append('}')

        r.append('function promptRename() {')
        r.append('  let files = getSelectedFiles();')
        r.append('  if (files.length !== 1) { alert("Please select exactly one item to rename."); return; }')
        r.append('  let oldName = files[0];')
        r.append('  let newName = prompt("Enter new name:", oldName);')
        r.append('  if (newName && newName !== oldName) {')
        r.append('    fetch("/", {')
        r.append('      method: "POST",')
        r.append('      headers: { "Content-Type": "application/json" },')
        r.append('      body: JSON.stringify({ action: "rename", abs_path: document.getElementById("currentAbsPath").value, old_name: oldName, new_name: newName })')
        r.append('    }).then(res => res.json()).then(data => { if(data.error) alert(data.error); else location.reload(); });')
        r.append('  }')
        r.append('}')

        r.append('function prepareCreateCBZ() {')
        r.append('  let files = getSelectedFiles(); if(files.length < 2) { alert("Select at least 2 files."); return; }')
        r.append('  let outputDiv = document.getElementById("executionOutput"); let contentDiv = document.getElementById("outputContent");')
        r.append('  outputDiv.style.display = "block"; contentDiv.innerText = "Processing...";')
        r.append('  fetch("/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ abs_path: document.getElementById("currentAbsPath").value, pattern: files[0].split(" ")[0] + "*.*", outname: files[0].split(" ")[0] + " v01" }) })')
        r.append('  .then(res => res.json()).then(data => { contentDiv.innerText = data.output || data.error; setTimeout(() => location.reload(), 3000); });')
        r.append('}')
        
        r.append('function toggleSelectAll() { let chks = document.querySelectorAll(".item-chk"); let state = !chks[0].checked; chks.forEach(c => c.checked = state); updateSelectedFiles(); }')
        r.append('function saveFolderScroll(n) { sessionStorage.setItem("scrollTarget", n); }')
        r.append('</script></body></html>')
        
        encoded = '\n'.join(r).encode(enc, 'surrogateescape')
        self.send_response(200)
        self.send_header("Content-type", f"text/html; charset={enc}")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("target_dir", nargs="?", default=".")
    args = parser.parse_args()
    
    os.chdir(args.target_dir)
    server_address = ('', 8123)
    httpd = HTTPServer(server_address, CustomHandler)
    print(f"Serving at http://localhost:8123/")
    httpd.serve_forever()