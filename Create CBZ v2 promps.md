# Create CBZ v2 Prompts

The following prompts guided the development and refinement of the merging script.

## Phase 1: Core Logic
> "Create a python script that takes all .cbz and .cbr files in a folder, extracts them into temporary subdirectories, and then zips everything back up into a single new .cbz named after the parent folder. Clean up the temp folders afterward."

## Phase 2: Patterns and Custom Naming
> "Add support for command line arguments: one for a wildcard pattern (to filter which files to merge) and one for the output filename."

## Phase 3: Simulation Mode
> "Add a --dry-run flag. When active, the script should print exactly which directories it would create, which files it would extract, and which files it would delete, but it should not change anything on the disk."

## Phase 4: Clean Dry-Run
> "Fix the dry-run behavior: Ensure that no directories (like 'makecbz_working_temp') are created at all during a simulation. The script should be completely read-only when --dry-run is used."
