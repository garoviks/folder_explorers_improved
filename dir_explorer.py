import os
import sys
import urllib.parse
import html
import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer

class CustomHandler(SimpleHTTPRequestHandler):
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
        r.append('h1 { margin: 0; }')
        r.append('</style>')
        r.append('</head>\n<body>')
        
        num_dirs = sum(1 for name in list_dir if os.path.isdir(os.path.join(path, name)))
        num_files = len(list_dir) - num_dirs
        
        r.append('<div class="header-container">')
        r.append(f'<h1>{title}</h1>')
        r.append(f'<button class="count-btn" onclick="alert(\'This folder contains {num_files} files and {num_dirs} folders.\')">Show Item Count</button>')
        r.append('</div>')
        r.append('<table>')
        r.append('<tr><th>Name</th><th>Size</th><th>Modified</th></tr>')
        
        if self.path != '/':
            r.append('<tr><td><a href="../" class="dir">📁 ../ (Parent Directory)</a></td><td>-</td><td>-</td></tr>')

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
                
            linkname = urllib.parse.quote(linkname, errors='surrogatepass')
            escaped_displayname = html.escape(displayname)
            
            r.append(f'<tr><td><a href="{linkname}" {a_class}>{escaped_displayname}</a></td><td>{size_str}</td><td>{mtime}</td></tr>')
            
        r.append('</table>\n</body>\n</html>\n')
        
        encoded = '\n'.join(r).encode(enc, 'surrogateescape')
        
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
