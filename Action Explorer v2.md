# Action Explorer v2

An interactive, web-based directory explorer designed for comic archive management.

## Key Features
- **Dark-Themed UI**: Modern, responsive interface for browsing local directories.
- **Intelligent Selection**:
  - Checkboxes next to all files/folders.
  - "Select/Deselect All" button.
  - **Volume Skipping**: Automatically ignores files labeled 'v01', 'Vol 1', etc., during batch selection to prevent accidental merging of Trade Paperbacks.
- **Smart Directory Info**:
  - **Items Column**: Shows the number of items inside subfolders.
  - **Tooltips**: Hover over the item count to see the breakdown (e.g., "8 files, 2 folders").
- **Live Command Execution**:
  - **Show Selected**: Summarizes selected files and previews the exact `makecbz.py` command.
  - **Real-Time Console**: When "Create CBZ" is clicked, a dedicated terminal-style console slides into view.
  - **Live Output**: Streams `stdout` and `stderr` from the server to the browser so you can watch the merge progress.
- **Advanced Navigation**:
  - **Scroll Restoration**: Remembers your scroll position when you navigate into a subfolder and back.
  - **Highlighting**: Briefly highlights the folder you just returned from in yellow.
  - **Auto-Refresh**: Automatically reloads the file list 2.5 seconds after a successful merge operation.

## Architecture
- **Backend**: Python `HTTPServer` with a custom `do_POST` handler for executing system commands.
- **Frontend**: Vanilla HTML/CSS/JavaScript. No external dependencies or frameworks required.

---

## Retrospective: Version 1
The original version (v01) served as a streamlined directory browser. It featured:
- **Clean Table Layout**: Simplified list of folders and files.
- **Core Metadata**: Displayed only filename, file size, and modification timestamp.
- **Dark Theme Foundations**: Established the consistent dark visual style.
- **Basic Navigation**: Clickable directory links for traversing the local filesystem.
