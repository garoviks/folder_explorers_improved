import argparse
import re
import csv
from pathlib import Path

# Pre-compile Regular Expressions
NUMBERED_PATTERN = re.compile(r'0\d|00\d')
SKIP_PATTERN = re.compile(r'v0\d|v\d|vol\.?\s?\d|t\s?\d|book\s?\d', re.IGNORECASE)
SERIES_NAME_PATTERN = re.compile(r'(\s|#)(0{1,2})?\d.*\.cb[rz]', re.IGNORECASE)
YEAR_PATTERN = re.compile(r'\((\d{4})\)')

def has_subdirectories(path: Path) -> bool:
    """Checks if a given path contains any subdirectories."""
    try:
        for entry in path.iterdir():
            if entry.is_dir():
                return True
        return False
    except OSError as e:
         
        return False

def get_comic_files_in_dir(folder_path: Path):
    """Returns a list of comic file names in the directory."""
    comic_files = []
    try:
        for file_entry in folder_path.iterdir():
            if file_entry.is_file() and file_entry.name.lower().endswith((".cbz", ".cbr")):
                comic_files.append(file_entry.name)
        return comic_files
    except OSError as e:
        print(f"Error scanning directory '{folder_path}' for files: {e}")
        return []

def group_comics_by_series(comic_files):
    """Groups a list of comic files by their series name and extracts years."""
    series_groups = {}
    for comic_file in comic_files:
        # Patterns for numbered issues that should be included
        numbered_pattern_match = NUMBERED_PATTERN.search(comic_file)

        # Patterns to skip, as they likely indicate an existing comic volume
        skip_pattern_match = SKIP_PATTERN.search(comic_file)

        if numbered_pattern_match and not skip_pattern_match:
            # Extract the comic series name and potential year
            series_name = SERIES_NAME_PATTERN.sub('', comic_file).strip()
            year_match = YEAR_PATTERN.search(comic_file)
            year = int(year_match.group(1)) if year_match else None

            if series_name not in series_groups:
                series_groups[series_name] = {'files': [], 'years': set()}

            series_groups[series_name]['files'].append(comic_file)
            if year:
                series_groups[series_name]['years'].add(year)
                
    return series_groups

def generate_volume_metadata(folder_path: Path, series_name, data, min_files, max_files):
    """Generates the metadata to be written to the CSV file for a given series."""
    sorted_files = sorted(data['files'])
    file_count = len(sorted_files)

    # Determine the makecbz value based on the file count
    makecbz_first_row_value = ""
    if file_count > max_files:
        makecbz_first_row_value = "M"
    elif file_count < min_files:
        makecbz_first_row_value = "S"
    else:
        makecbz_first_row_value = "Y"

    highest_year = max(data['years']) if data['years'] else None

    # Construct the base volume name
    base_volume_name = f"{series_name} v01"
    if highest_year:
        base_volume_name += f" ({highest_year})"
    base_volume_name += ".cbz"

    # Prepend the full folder path to the volume name
    full_volume_name = folder_path / base_volume_name

    # Construct the comic pattern
    comic_pattern = f"{series_name}*.*"

    results = []
    first_row_for_series = True
    
    for file_name in sorted_files:
        full_path = folder_path / file_name
        makecbz_value = makecbz_first_row_value if first_row_for_series else ""
        results.append((
            str(folder_path), 
            str(full_path), 
            comic_pattern, 
            str(full_volume_name), 
            makecbz_value
        ))

        if first_row_for_series:
            print(f"    - Identified: {file_name}")
            print(f"      Suggested Volume: {full_volume_name}")
            print(f"      File Pattern: {comic_pattern}")
            print(f"      Make CBZ: {makecbz_first_row_value}")
            first_row_for_series = False
        else:
            print(f"    - Identified: {file_name}")
            
    return results

def process_folder(folder_path: Path, csv_writer, min_files: int, max_files: int):
    """Processes a single folder for comic files and streams results to CSV."""
    comic_files = get_comic_files_in_dir(folder_path)

    if len(comic_files) > 1:
        print(f"  Found multiple comic files in: {folder_path}")
        series_groups = group_comics_by_series(comic_files)

        for series_name, data in series_groups.items():
            if data['files']:
                rows = generate_volume_metadata(folder_path, series_name, data, min_files, max_files)
                for row in rows:
                    csv_writer.writerow(row)

    elif len(comic_files) == 1:
        print(f"  Only one comic file found in '{folder_path}', skipping numbering check.")

def scan_folders_for_comics(output_filename: str, min_files: int, max_files: int, scan_dir: str = "."):
    """
    Scans folders (one level deep) for .cbz or .cbr files, identifies numbered files
    in folders with multiple comic files, skips specific file patterns,
    skips folders with subfolders, and writes identified/skipped lists to CSVs.
    """
    current_directory = Path(scan_dir).resolve()
    print(f"Scanning from: {current_directory} (one level deep)")

    # Determine the skipped output file name
    output_path = Path(output_filename)
    skipped_output_filename = f"{output_path.stem}_skipped{output_path.suffix}"
    if not output_path.suffix:
        skipped_output_filename = f"{output_filename}_skipped.csv"
        
    skipped_folders_info = []

    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as main_csvfile:
            writer = csv.writer(main_csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(["folder_name", "full_file_name", "comic_pattern", "comic_volume_name", "makecbz"])
            
            # --- Process the current_directory itself ---
            if not has_subdirectories(current_directory):
                process_folder(current_directory, writer, min_files, max_files)
            else:
                print(f"  Skipping current directory '{current_directory}' because it contains subfolders.")

            # --- Process direct subfolders of current_directory ---
            try:
                for entry in current_directory.iterdir():
                    if entry.is_dir():
                        if has_subdirectories(entry):
                            print(f"  Skipping subfolder '{entry}' because it contains subfolders.")
                            try:
                                for sub_sub_entry in entry.iterdir():
                                    if sub_sub_entry.is_dir():
                                        skipped_folders_info.append((str(entry), sub_sub_entry.name))
                            except OSError as e:
                                print(f"Error scanning subfolder '{entry}' for sub-subfolders: {e}")
                        else:
                            process_folder(entry, writer, min_files, max_files)
            except OSError as e:
                print(f"Error scanning current directory '{current_directory}' for direct subfolders: {e}")
                
        print(f"\nResults successfully written to '{output_filename}'")
    except IOError as e:
        print(f"Error writing to file '{output_filename}': {e}")

    # Write the skipped folders to the _skipped CSV file
    if skipped_folders_info:
        try:
            with open(skipped_output_filename, 'w', newline='', encoding='utf-8') as skipped_csvfile:
                skipped_writer = csv.writer(skipped_csvfile, quoting=csv.QUOTE_ALL)
                skipped_writer.writerow(["folder_name", "subfolder_name"])
                for folder_path, subfolder_name in skipped_folders_info:
                    skipped_writer.writerow([folder_path, subfolder_name])
            print(f"Skipped folders successfully written to '{skipped_output_filename}'")
        except IOError as e:
            print(f"Error writing to skipped file '{skipped_output_filename}': {e}")
    else:
        print(f"No folders were skipped due to containing subfolders. '{skipped_output_filename}' not created.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scan folders (one level deep) for comic files (.cbz/.cbr) and list "
                     "files with specific numbering patterns, skipping folders with subfolders "
                     "and files with certain volume patterns. Also lists skipped folders."
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        default="a_folders2cbz.csv",
        help="Base name of the result CSV file (e.g., my_comics.csv). "
             "Defaults to 'a_folders2cbz.csv'. "
             "A '_skipped' version will also be created for skipped folders."
    )
    parser.add_argument(
        "--min-files",
        type=int,
        default=4,
        help="Threshold (minimum) for 'S' flag. Default is 4."
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=6,
        help="Threshold (maximum) for 'M' flag. Default is 6."
    )

    parser.add_argument(
        "--scan-dir",
        type=str,
        default=".",
        help="The directory to scan. Defaults to the current directory."
    )

    args = parser.parse_args()
    scan_folders_for_comics(args.output_file, args.min_files, args.max_files, args.scan_dir)
