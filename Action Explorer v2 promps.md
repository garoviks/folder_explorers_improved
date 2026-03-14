# Action Explorer v2 Prompts

The following prompts illustrate the evolution of the script from a basic directory lister to a specialized management tool.

## Phase 1: Interactive Selection
> "Modify action_explorer.py to add checkboxes next to each file. Add a button to 'Show Selected' which alerts the names of the files I've checked. Ensure the 'Select/Deselect All' button works correctly."

## Phase 2: Grouping & Pattern Detection
> "Implement logic to detect series names. If I have 'Comic 01.cbz' and 'Comic 02.cbz', identify the group as 'Comic'. Add a 'Create CBZ' button that generates a command string using makecbz.py with the detected pattern and a proposed output name like 'Comic v01'."

## Phase 3: Volume Filtering
> "Add a rule to the selection logic: do not auto-select files that appear to be compiled volumes (e.g., filenames containing v01, Vol 1, T01, Book 1). Use word boundaries to avoid matching strings like 'Volume' inside a series title."

## Phase 4: Dynamic Metrics
> "Add a column called 'Items'. For folders, it should show the count of items inside. Add a hover tooltip that shows how many files vs how many folders are in that subdirectory."

## Phase 5: Live Terminal & Server Backend
> "Add a POST handler to the Python server. When I click 'Create CBZ', instead of a popup, open a console area at the bottom of the page. Send the command to the server, execute it, and stream the terminal logs back to that console UI."

## Phase 6: Navigation Polish
> "Implement scroll restoration. When I click a folder and then come back, the page should automatically scroll to the folder I just visited and briefly highlight it. Ensure it works on Firefox by using the 'pageshow' event."

---

## Origins: Version 1 Prompts
The project began as a simple utility to visualize folder contents. The foundational prompt was:

> "Create a Python HTTP server that serves a custom directory listing for a specific path. It should have a dark aesthetic, use standard table columns (Name, Size, Modified), and allow me to navigate up and down through folders using clickable links."
