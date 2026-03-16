"""
Script: action_explorer.py
Version: v03
Description: A custom HTTP web server that provides an interactive directory listing. 
It displays folder contents with sizes and modification dates in a dark-themed UI, 
and includes interactive features to count items and generate/copy terminal commands 
for creating CBZ archives using makecbz.py.
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
        
        abs_path = data.get('abs_path')
        pattern = data.get('pattern')
        outname = data.get('outname')
        
        # Security: ensure we are running on the system
        try:
            # Change to the target directory
            cwd = os.getcwd()
            os.chdir(abs_path)
            
            # Prepare the command
            cmd = ["python3", "/home/nesha/scripts/makecbz.py", pattern, outname]
            
            # Execute
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
        
        # Sort directories first, then files, both alphabetically
        list_dir.sort(key=lambda a: (not os.path.isdir(os.path.join(path, a)), a.lower()))
        
        displaypath = html.escape(urllib.parse.unquote(self.path))
        
        enc = sys.getfilesystemencoding()
        title = f'Directory listing for {displaypath}'
        
        r = []
        r.append('<!DOCTYPE HTML>')
        r.append('<html>\n<head>')
        r.append(f'<meta charset="{enc}">')
        r.append(f'<title>{title}</title>')
        r.append('<style>')
        r.append('body { font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 2rem; background: #121212; color: #e0e0e0; }')
        r.append('h1 { color: #ffffff; }')
        r.append('table { width: 100%; border-collapse: collapse; background: #1e1e1e; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }')
        r.append('th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #333; }')
        r.append('th { background: #2c2c2c; font-weight: 600; color: #ffffff; }')
        r.append('tr:hover { background: #2a2a2a; }')
        r.append('tr:last-child td { border-bottom: none; }')
        r.append('a { color: #64b5f6; text-decoration: none; font-weight: 500; display: block; }')
        r.append('a:hover { color: #90caf9; text-decoration: underline; }')
        r.append('.dir { color: #81c784; font-weight: bold; }')
        r.append('.dir:hover { color: #a5d6a7; }')
        r.append('.count-btn { background-color: #4CAF50; border: none; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; cursor: pointer; border-radius: 4px; margin-left: 10px; }')
        r.append('.count-btn:hover { background-color: #45a049; }')
        r.append('.header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }')
        r.append('.button-group { display: flex; gap: 10px; }')
        r.append('.modal { display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }')
        r.append('.modal-content { background-color: #1e1e1e; margin: 15% auto; padding: 20px; border: 1px solid #888; width: 50%; border-radius: 8px; color: white; text-align: center; }')
        r.append('.close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }')
        r.append('.close:hover { color: white; }')
        r.append('  .cmd-box { background: #eee; padding: 10px; font-family: monospace; overflow-x: auto; white-space: pre-wrap; margin-bottom: 20px; border-left: 5px solid #ccc; }')
        r.append('  #executionOutput { display: none; margin-top: 30px; background: #1e1e1e; color: #d4d4d4; padding: 15px; font-family: "Courier New", Courier, monospace; border-radius: 5px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; box-shadow: inset 0 0 10px #000; border: 1px solid #333; }')
        r.append('  #executionOutput h3 { color: #569cd6; margin-top: 0; font-size: 1em; border-bottom: 1px solid #333; padding-bottom: 5px; }')
        r.append('h1 { margin: 0; }')
        r.append('</style>')
        r.append('</head>\n<body>')
        
        num_dirs = sum(1 for name in list_dir if os.path.isdir(os.path.join(path, name)))
        num_files = len(list_dir) - num_dirs
        
        abs_path = os.path.abspath(path)
        # makecbz.py operates on its current working directory.
        cmd_str = f'cd "{abs_path}" && python3 "/home/nesha/scripts/makecbz.py" --dry-run'
        
        r.append('<div class="header-container">')
        r.append('<div style="display: flex; align-items: center; gap: 15px;">')
        r.append(f'<button class="count-btn" onclick="toggleSelectAll()">Select/Deselect All</button>')
        r.append(f'<h1>{title}</h1>')
        r.append('</div>')
        r.append('<div class="button-group">')
        r.append(f'<input type="hidden" id="currentAbsPath" value="{html.escape(abs_path)}">')
        r.append('<button class="count-btn" onclick="showSelected()">Show Selected</button>')
        r.append('<button class="count-btn" onclick="prepareCreateCBZ()">Create CBZ</button>')
        r.append('</div>')
        r.append('</div>')
        r.append('<table>')
        r.append('<tr><th style="width: 30px;"></th><th>Name</th><th>Items</th><th>Size</th><th>Modified</th></tr>')
        
        if self.path != '/':
            r.append('<tr><td></td><td><a href="../" class="dir">📁 ../ (Parent Directory)</a></td><td>-</td><td>-</td><td>-</td></tr>')

        for name in list_dir:
            fullname = os.path.join(path, name)
            displayname = name
            linkname = name
            
            is_dir = os.path.isdir(fullname)
            
            if is_dir:
                displayname = "📁 " + name + "/"
                linkname = name + "/"
                a_class = 'class="dir"'
            else:
                displayname = "📄 " + name
                a_class = ''
            
            try:
                stat = os.stat(fullname)
                size = stat.st_size
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                if is_dir:
                    size_str = '-'
                else:
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f} KB"
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    else:
                        size_str = f"{size/(1024*1024*1024):.1f} GB"
                        
            except OSError:
                size_str = '-'
                mtime = '-'
            
            # Count items in subdirectory
            items_str = '-'
            items_title = ''
            if is_dir:
                try:
                    sub_entries = os.listdir(fullname)
                    sub_files = sum(1 for e in sub_entries if os.path.isfile(os.path.join(fullname, e)))
                    sub_dirs = sum(1 for e in sub_entries if os.path.isdir(os.path.join(fullname, e)))
                    total = sub_files + sub_dirs
                    items_str = str(total)
                    items_title = f'{sub_files} file(s), {sub_dirs} folder(s)'
                except OSError:
                    items_str = '?'
                    items_title = 'Cannot read folder'
                
            linkname = urllib.parse.quote(linkname, errors='surrogatepass')
            escaped_displayname = html.escape(displayname)
            
            is_dir_str = "true" if is_dir else "false"
            chk_box = f'<input type="checkbox" class="item-chk" value="{html.escape(name)}" data-isdir="{is_dir_str}" onchange="updateSelectedFiles()">'
            
            # Sanitize name for use as an HTML id
            row_id = html.escape(name).replace(' ', '_').replace('(', '').replace(')', '').replace('.', '_').replace("'", '').replace('&', '').replace('+', '').replace(',', '')
            
            if is_dir:
                r.append(f'<tr id="row-{row_id}"><td>{chk_box}</td><td><a href="{linkname}" {a_class} onclick="saveFolderScroll(\'{html.escape(name)}\')">{escaped_displayname}</a></td><td title="{items_title}" style="color:#555;font-size:0.9em">{items_str}</td><td>{size_str}</td><td>{mtime}</td></tr>')
            else:
                r.append(f'<tr id="row-{row_id}"><td>{chk_box}</td><td><a href="{linkname}" {a_class}>{escaped_displayname}</a></td><td>-</td><td>{size_str}</td><td>{mtime}</td></tr>')
            
        r.append('</table>\n')
        
        # Modal HTML
        r.append('<div id="cmdModal" class="modal">')
        r.append('  <div class="modal-content">')
        r.append('    <span class="close" onclick="closeModal()">&times;</span>')
        r.append('    <h2>Run this command:</h2>')
        r.append('    <div id="cmdText" class="cmd-box"></div>')
        r.append('    <button class="count-btn" onclick="copyModalCmd()">Copy Command</button>')
        r.append('  </div>')
        r.append('</div>')
        
        r.append('<div id="executionOutput">')
        r.append('  <h3>Terminal Output</h3>')
        r.append('  <div id="outputContent"></div>')
        r.append('</div>')
        
        # Scripts
        r.append('<script>')
        r.append('function showModal(cmd) {')
        r.append('  document.getElementById("cmdText").innerText = cmd;')
        r.append('  document.getElementById("cmdModal").style.display = "block";')
        r.append('}')
        r.append('function closeModal() {')
        r.append('  document.getElementById("cmdModal").style.display = "none";')
        r.append('}')
        r.append('function copyModalCmd() {')
        r.append('  var text = document.getElementById("cmdText").innerText;')
        r.append('  navigator.clipboard.writeText(text).then(function() {')
        r.append('    alert("Command copied to clipboard!");')
        r.append('    closeModal();')
        r.append('  }).catch(function(err) {')
        r.append('    alert("Failed to copy command: " + err);')
        r.append('  });')
        r.append('}')
        r.append('window.onclick = function(event) {')
        r.append('  var modal = document.getElementById("cmdModal");')
        r.append('  if (event.target == modal) {')
        r.append('    closeModal();')
        r.append('  }')
        r.append('}')
        
        r.append('function saveFolderScroll(folderName) {')
        r.append('  sessionStorage.setItem("scrollTarget:" + window.location.pathname, folderName);')
        r.append('}')
        r.append('window.addEventListener("pageshow", function(event) {')
        r.append('  let key = "scrollTarget:" + window.location.pathname;')
        r.append('  let target = sessionStorage.getItem(key);')
        r.append('  if (target) {')
        r.append('    sessionStorage.removeItem(key);')
        r.append('    let rows = document.querySelectorAll("tr");')
        r.append('    for (let row of rows) {')
        r.append('      let link = row.querySelector("a");')
        r.append('      if (link && link.textContent.trim().replace(/^📁\\s*/, "").replace(/\\/$/, "") === target) {')
        r.append('        setTimeout(function() {')
        r.append('          row.scrollIntoView({ behavior: "smooth", block: "center" });')
        r.append('          row.style.transition = "background 0.5s";')
        r.append('          row.style.background = "#fffbcc";')
        r.append('          setTimeout(() => { row.style.background = ""; }, 2000);')
        r.append('        }, 50);')
        r.append('        break;')
        r.append('      }')
        r.append('    }')
        r.append('  }')
        r.append('});')
        r.append('function hideWarning() {')
        r.append('  let warningDiv = document.getElementById("topWarning");')
        r.append('  if (warningDiv) warningDiv.style.display = "none";')
        r.append('}')
        
        r.append('let selectedFiles = new Set();')
        
        r.append('function isVolume(name) {')
        r.append('  const skipPattern = /\\b(?:v\\d|vol\\.?\\s*\\d|t\\s*\\d|book\\s*\\d)\\b/i;')
        r.append('  return skipPattern.test(name);')
        r.append('}')
        
        r.append('function updateSelectedFiles() {')
        r.append('  hideWarning();')
        r.append('  selectedFiles.clear();')
        r.append('  const checkboxes = document.querySelectorAll(".item-chk");')
        r.append('  checkboxes.forEach(chk => {')
        r.append('    const name = chk.value;')
        r.append('    if (chk.checked && chk.getAttribute("data-isdir") === "false") {')
        r.append('      if (!isVolume(name)) {')
        r.append('        selectedFiles.add(name);')
        r.append('      } else {')
        r.append('        chk.checked = false; // Uncheck volumes automatically')
        r.append('      }')
        r.append('    }')
        r.append('  });')
        r.append('  console.log("Internally tracking selected files:", Array.from(selectedFiles));')
        r.append('}')
        
        r.append('function toggleSelectAll() {')
        r.append('  const checkboxes = document.querySelectorAll(".item-chk");')
        r.append('  let allChecked = true;')
        r.append('  checkboxes.forEach(chk => {')
        r.append('    if (!chk.checked) allChecked = false;')
        r.append('  });')
        r.append('  checkboxes.forEach(chk => {')
        r.append('    chk.checked = !allChecked;')
        r.append('  });')
        r.append('  updateSelectedFiles();')
        r.append('}')
        
        r.append('function getSelectedFiles() {')
        r.append('  let files = Array.from(selectedFiles);')
        r.append('  if (files.length === 0) {')
        r.append('    const checkboxes = document.querySelectorAll(".item-chk");')
        r.append('    checkboxes.forEach(chk => {')
        r.append('      const name = chk.value;')
        r.append('      if (chk.getAttribute("data-isdir") === "false" && !isVolume(name)) {')
        r.append('        files.push(name);')
        r.append('      }')
        r.append('    });')
        r.append('  }')
        r.append('  return files;')
        r.append('}')
        
        r.append('function showSelected() {')
        r.append('  hideWarning();')
        r.append('  let files = getSelectedFiles();')
        if_no_files = '  if (files.length === 0) { alert("No files available!"); return; }'
        r.append(if_no_files)
        
        r.append('  let cmdInfo = generateCBZParams(files);')
        r.append('  let msg = "Selected files:\\n\\n" + files.join("\\n");')
        r.append('  if (cmdInfo && !cmdInfo.warning) {')
        r.append('    let absPath = document.getElementById("currentAbsPath").value;')
        r.append('    let fullCmd = `python3 "/home/nesha/scripts/makecbz.py" "${cmdInfo.pattern}" "${cmdInfo.outname}"`;')
        r.append('    msg += "\\n\\nProposed Command:\\n" + fullCmd;')
        r.append('  }')
        r.append('  alert(msg);')
        r.append('}')
        
        r.append('function getGroupName(filename) {')
        r.append('  let name = filename.replace(/\\.(cbz|cbr|zip|rar)$/i, "");')
        r.append('  // 1. Try leading zero (standard issue format: Archangel 8 01 -> Archangel 8)')
        r.append('  let match = name.match(/(?:\\s|-|#|_)+(0\\d+)/i);')
        r.append('  if (match) {')
        r.append('    return name.substring(0, name.indexOf(match[0])).trim();')
        r.append('  }')
        r.append('  // 2. Fallback: First number followed by a separator (Reality Show 1. -> Reality Show)')
        r.append('  match = name.match(/(?:\\s|-|#|_)+(\\d+)(?:[\\.\\s-_]+|$)/i);')
        r.append('  if (match) {')
        r.append('    return name.substring(0, name.indexOf(match[0])).trim();')
        r.append('  }')
        r.append('  return name;')
        r.append('}')
        
        r.append('function generateCBZParams(files) {')
        r.append('  if (files.length <= 1) return null;')
        r.append('  let groups = new Set();')
        r.append('  files.forEach(f => groups.add(getGroupName(f)));')
        r.append('  ')
        r.append('  if (groups.size > 1) {')
        r.append('    return { warning: true, groups: Array.from(groups) };')
        r.append('  }')
        r.append('  let groupPrefix = Array.from(groups)[0];')
        r.append('  return {')
        r.append('    pattern: groupPrefix + "*.*",')
        r.append('    outname: groupPrefix + " v01"')
        r.append('  };')
        r.append('}')
        
        r.append('function prepareCreateCBZ() {')
        r.append('  let files = getSelectedFiles();')
        r.append('  if (files.length <= 1) {')
        r.append('    alert("At least two files must be selected to create a merged CBZ!"); return;')
        r.append('  }')
        r.append('  let cmdInfo = generateCBZParams(files);')
        r.append('  let warningDiv = document.getElementById("topWarning");')
        r.append('  if (warningDiv) warningDiv.style.display = "none";')
        r.append('  ')
        r.append('  if (cmdInfo.warning) {')
        r.append('    if (!warningDiv) {')
        r.append('      warningDiv = document.createElement("div");')
        r.append('      warningDiv.id = "topWarning";')
        r.append('      warningDiv.style.backgroundColor = "#ff9800";')
        r.append('      warningDiv.style.color = "black";')
        r.append('      warningDiv.style.padding = "10px";')
        r.append('      warningDiv.style.marginBottom = "15px";')
        r.append('      warningDiv.style.textAlign = "center";')
        r.append('      warningDiv.style.fontWeight = "bold";')
        r.append('      document.body.insertBefore(warningDiv, document.body.firstChild);')
        r.append('    }')
        r.append('    warningDiv.innerText = "WARNING: More than one file group detected: " + cmdInfo.groups.map(s => "\\"" + s + "\\"").join(", ");')
        r.append('    warningDiv.style.display = "block";')
        r.append('    return;')
        r.append('  }')
        r.append('  ')
        r.append('  let absPath = document.getElementById("currentAbsPath").value;')
        r.append('  let outputDiv = document.getElementById("executionOutput");')
        r.append('  let contentDiv = document.getElementById("outputContent");')
        r.append('  ')
        r.append('  outputDiv.style.display = "block";')
        r.append('  contentDiv.innerText = "Executing command...\\n";')
        r.append('  outputDiv.scrollIntoView({ behavior: "smooth" });')
        r.append('  ')
        r.append('  fetch("/", {')
        r.append('    method: "POST",')
        r.append('    headers: { "Content-Type": "application/json" },')
        r.append('    body: json_stringify({')
        r.append('      abs_path: absPath,')
        r.append('      pattern: cmdInfo.pattern,')
        r.append('      outname: cmdInfo.outname')
        r.append('    })')
        r.append('  })')
        r.append('  .then(response => response.json())')
        r.append('  .then(data => {')
        r.append('    if (data.error) {')
        r.append('      contentDiv.innerText += "ERROR: " + data.error;')
        r.append('    } else {')
        r.append('      contentDiv.innerText += data.output;')
        r.append('      contentDiv.innerText += "\\n\\n--- Command Finished. Refreshing list in 2.5 seconds... ---";')
        r.append('      setTimeout(() => { location.reload(); }, 2500);')
        r.append('    }')
        r.append('  })')
        r.append('  .catch(err => {')
        r.append('    contentDiv.innerText += "CONNECTION ERROR: " + err;')
        r.append('  });')
        r.append('}')
        r.append('</script>')
        
        r.append('</body>\n</html>\n')
        
        encoded = '\n'.join(r).replace('json_stringify', 'JSON.stringify').encode(enc, 'surrogateescape')
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        
        self.wfile.write(encoded)
        return None

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Serve a directory with a custom HTML index.")
    parser.add_argument("target_dir", nargs="?", default=".", help="The directory to serve (default: current directory)")
    args = parser.parse_args()

    port = 8123
    target_dir = args.target_dir
    
    # Change into the target directory first
    try:
        os.chdir(target_dir)
    except Exception as e:
        print(f"Failed to chdir to {target_dir}: {e}")
        sys.exit(1)
        
    server_address = ('', port)
    httpd = HTTPServer(server_address, CustomHandler)
    print(f"Serving {target_dir} at http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()
