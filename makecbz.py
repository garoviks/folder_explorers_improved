#!/usr/bin/env python3

# ==============================================================================
# Script Name:      makecbz.py
# Description:      Extracts and then merges multiple .cbz/.cbr archives into
#                   a single new .cbz file, followed by a cleanup of original
#                   files and temporary folders.
# Version:          v02
# Usage:            python3 makecbz.py [pattern] [output_name]
#                   If no arguments are provided, it defaults to processing
#                   all *.cbz and *.cbr files in the current directory,
#                   naming the output after the current folder.
# Requirements:     'unzip', 'unrar', and 'zip' must be installed and in your PATH.
# ==============================================================================

import os
import sys
import argparse
from pathlib import Path
import subprocess
import shutil
import fnmatch


def check_dependencies():
    """Checks if the required external commands are available."""
    required_cmds = ['unzip', 'unrar', 'zip']
    for cmd in required_cmds:
        try:
            # Use '--version' or a similar non-destructive option to check if command runs
            subprocess.run([cmd, '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Error: Required command '{cmd}' is not installed or not in your PATH.", file=sys.stderr)
            sys.exit(1)


def get_arguments():
    """Parses command-line arguments using argparse."""
    parser = argparse.ArgumentParser(
        description="Merges comic archives into a single .cbz file."
    )
    parser.add_argument(
        'pattern',
        nargs='?',
        default=None,
        help="A wildcard pattern for the files to process (case-sensitive for filenames)."
    )
    parser.add_argument(
        'output_name',
        nargs='?',
        default=None,
        help="The name for the resulting .cbz file (without extension)."
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Simulation mode: display what would be done without making any actual changes."
    )
    return parser.parse_args()


def determine_paths_and_names(args):
    """
    Determines current folder, final output CBZ name, destination directory for the final CBZ,
    the dedicated temporary directory for extractions, and the list of files to process.
    """
    current_folder = Path.cwd()
    current_folder_name = current_folder.name

    # Determine the base name for the output CBZ file
    if args.output_name:
        output_name_base = args.output_name
    else:
        output_name_base = current_folder_name
    final_output_cbz_name = f"{output_name_base}.cbz"

    is_output_folder_created = False
    # Determine the destination directory for the final output CBZ file
    # If pattern AND output_name are provided, the final CBZ goes into a new folder named after output_name.
    # Otherwise, it goes into the current folder.
    if args.pattern and args.output_name:
        final_output_destination_dir = current_folder / output_name_base
        if not args.dry_run:
            os.makedirs(final_output_destination_dir, exist_ok=True)
        is_output_folder_created = True  # Set flag if a new output folder is created
        print(f"Final merged CBZ will be placed temporarily in: '{final_output_destination_dir}'")
    else:
        final_output_destination_dir = current_folder
        print(f"Final merged CBZ will be placed in the current folder: '{final_output_destination_dir}'")

    # Create a dedicated temporary directory for all extractions
    # This ensures original archives are not in the same directory as extracted content during zipping
    temp_extraction_root_dir = current_folder / "makecbz_working_temp"
    if not args.dry_run:
        os.makedirs(temp_extraction_root_dir, exist_ok=True)
        print(f"Temporary extraction directory created: '{temp_extraction_root_dir}'")
    else:
        print(f"  [DRY RUN] Would create temporary extraction directory: '{temp_extraction_root_dir}'")

    files_found = []

    # Collect all potential comic files ONLY from the current directory
    potential_comic_files = []

    # Iterate only through items in the current directory
    for item in current_folder.iterdir():
        if item.is_file():
            potential_comic_files.append(item)

    # Filter based on pattern (if provided) and comic extension (case-sensitive)
    for file_path in potential_comic_files:
        extension = file_path.suffix.lstrip('.').lower()
        if extension not in ("cbz", "cbr"):
            continue  # Not a comic file, skip

        if args.pattern:
            # If pattern is provided, match the filename against the pattern case-sensitively
            if fnmatch.fnmatch(file_path.name, args.pattern):
                files_found.append(file_path)
        else:
            # No pattern provided, just add all found comic files
            files_found.append(file_path)

    # Sort files to ensure consistent order in the output archive, sorting by full path
    files_to_process = sorted(files_found, key=str)  # Sort case-sensitively by default

    return current_folder, final_output_destination_dir, final_output_cbz_name, files_to_process, temp_extraction_root_dir, is_output_folder_created


def confirm_large_job(files):
    """Prompts the user for confirmation if the number of files is large."""
    file_count = len(files)
    if file_count > 20:
        print(f"Warning: You are about to process {file_count} files, which is a large number.")
        reply = input("Do you want to continue? (y/n): ").strip().lower()
        if reply != 'y':
            print("Script aborted by user.")
            sys.exit(0)


def extract_archives(files, temp_extraction_root_dir, dry_run=False):
    """Extracts all archives into temporary subdirectories within the temp_extraction_root_dir."""
    print("\n--- Starting Extraction Phase ---")
    extracted_subdirs = []
    original_files_to_delete = []

    for i, file_path in enumerate(files):
        if not file_path.is_file():
            print(f"Warning: File '{file_path.name}' not found. Skipping.", file=sys.stderr)
            continue

        # Create a temporary subfolder for each archive within temp_extraction_root_dir
        destination_dir = temp_extraction_root_dir / f"temp_extract_{i}_{file_path.stem}"
        if dry_run:
            print(f"  [DRY RUN] Would create directory: '{destination_dir}'")
        else:
            os.makedirs(destination_dir, exist_ok=True)

        extension = file_path.suffix.lstrip('.').lower()

        try:
            if extension in ("cbz", "zip"):
                print(f"Extracting .cbz archive: {file_path.name} to '{destination_dir.name}/'")
                command = ["unzip", "-o", "-q", str(file_path), "-d", str(destination_dir)]
                if dry_run:
                    print(f"  [DRY RUN] Would execute: {' '.join(command)}")
                else:
                    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                extracted_subdirs.append(destination_dir)
                original_files_to_delete.append(file_path)
            elif extension in ("cbr", "rar"):
                print(f"Extracting .cbr archive: {file_path.name} to '{destination_dir.name}/'")
                command = ["unrar", "e", "-o+", "-inul", str(file_path), str(destination_dir) + os.sep]
                if dry_run:
                    print(f"  [DRY RUN] Would execute: {' '.join(command)}")
                else:
                    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                extracted_subdirs.append(destination_dir)
                original_files_to_delete.append(file_path)
            else:
                print(f"Skipping '{file_path.name}': Not a .cbz or .cbr file.")
        except subprocess.CalledProcessError as e:
            print(f"Error extracting '{file_path.name}'. Command failed with exit code {e.returncode}.",
                  file=sys.stderr)
            if e.stderr:
                print(f"  Stderr: {e.stderr.decode()}", file=sys.stderr)
            # Clean up the partially extracted directory on error
            shutil.rmtree(destination_dir, ignore_errors=True)
            # Do not exit, try to process other files
        except Exception as e:
            print(f"An unexpected error occurred during extraction of '{file_path.name}': {e}", file=sys.stderr)
            shutil.rmtree(destination_dir, ignore_errors=True)

    print("Extraction complete.")
    return extracted_subdirs, original_files_to_delete


def create_merged_archive(temp_extraction_root_dir, final_output_cbz_name, final_output_destination_dir, current_folder,
                          is_output_folder_created, dry_run=False):
    """
    Consolidates extracted contents and creates the final .cbz archive,
    preserving internal directory structure. Handles moving the file if a dedicated
    output folder was used.
    """
    print("\n--- Starting Compression Phase ---")
    print(f"Creating a single archive: '{final_output_cbz_name}'")

    # Check if any content was actually extracted into the temporary root directory
    if not any(temp_extraction_root_dir.iterdir()) and not dry_run:
        print("No content found in the temporary extraction directory to create the new CBZ. Aborting compression.",
              file=sys.stderr)
        return False

    success = False
    original_cwd = Path.cwd()  # Save original working directory
    try:
        # Navigate to the dedicated temporary directory containing all extracted subfolders
        if not dry_run:
            os.chdir(temp_extraction_root_dir)

        # The final output CBZ will be created in the final_output_destination_dir
        absolute_output_path_temp = final_output_destination_dir / final_output_cbz_name

        command = ["zip", "-r", str(absolute_output_path_temp), "."]

        print(f"Executing zip command: {' '.join(command)}")
        if dry_run:
            print(f"  [DRY RUN] Would execute: {' '.join(command)}")
            success = True
        else:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print(f"Successfully created '{final_output_cbz_name}' in '{final_output_destination_dir}'.")
            success = True

        # If a dedicated output folder was created, move the merged archive to the current_folder
        if is_output_folder_created and final_output_destination_dir != current_folder:
            final_dest_in_current_folder = current_folder / final_output_cbz_name
            if dry_run:
                print(f"  [DRY RUN] Would move '{absolute_output_path_temp}' to '{final_dest_in_current_folder}'")
            else:
                shutil.move(absolute_output_path_temp, final_dest_in_current_folder)
            print(f"Moved '{final_output_cbz_name}' to '{current_folder}'.")

    except subprocess.CalledProcessError as e:
        print(f"Error zipping files. Command failed with exit code {e.returncode}.", file=sys.stderr)
        if e.stderr:
            print(f"  Stderr: {e.stderr.decode()}", file=sys.stderr)
    except FileNotFoundError:
        print("Error: 'zip' command not found. Please ensure it's installed and in your PATH.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred during compression or moving: {e}", file=sys.stderr)
    finally:
        # Always change back to the original working directory
        os.chdir(original_cwd)

    print("Compression complete.")
    return success


def cleanup(original_files_to_delete, temp_extraction_root_dir, final_output_destination_dir, current_folder,
            is_output_folder_created, dry_run=False):
    """Deletes original files, the entire temporary extraction directory, and the output folder if created and emptied."""
    print("\n--- Starting Cleanup Phase ---")

    # Delete the original comic archives
    for file_path in original_files_to_delete:
        print(f"Deleting original file: '{file_path.name}'")
        try:
            if dry_run:
                print(f"  [DRY RUN] Would delete '{file_path}'")
            else:
                os.remove(file_path)
        except OSError as e:
            print(f"Error deleting file '{file_path.name}': {e}", file=sys.stderr)

    # Delete the entire temporary extraction root directory
    if temp_extraction_root_dir.exists() or dry_run:
        print(f"Deleting temporary extraction folder: '{temp_extraction_root_dir}/'")
        try:
            if dry_run:
                print(f"  [DRY RUN] Would remove directory '{temp_extraction_root_dir}'")
            else:
                shutil.rmtree(temp_extraction_root_dir)
        except OSError as e:
            print(f"Error deleting directory '{temp_extraction_root_dir}/': {e}", file=sys.stderr)

    # If a dedicated output folder was created and the file was moved, delete the empty output folder
    if is_output_folder_created and (final_output_destination_dir.exists() or dry_run) and final_output_destination_dir != current_folder:
        # Check if the folder is empty or if the merged file is no longer there
        if dry_run or not any(final_output_destination_dir.iterdir()):
            print(f"Deleting created output folder: '{final_output_destination_dir}/'")
            try:
                if dry_run:
                    print(f"  [DRY RUN] Would remove directory '{final_output_destination_dir}'")
                else:
                    shutil.rmtree(final_output_destination_dir)
            except OSError as e:
                print(f"Error deleting directory '{final_output_destination_dir}/': {e}", file=sys.stderr)
        else:
            print(
                f"Output folder '{final_output_destination_dir}/' is not empty after moving the merged archive. Skipping deletion.",
                file=sys.stderr)

    print("Cleanup complete. 🧹")


def main():
    """Main function to orchestrate the script's execution."""
    # check_dependencies() # Commented out as requested

    args = get_arguments()
    dry_run = args.dry_run
    
    if dry_run:
        print("\n*** RUNNING IN DRY-RUN (SIMULATION) MODE ***\n")

    current_folder, final_output_destination_dir, final_output_cbz_name, files_to_process, temp_extraction_root_dir, is_output_folder_created = determine_paths_and_names(
        args)

    if not files_to_process:
        print("No .cbz or .cbr files found to process. Exiting. ")
        sys.exit(0)

    # Handle existing output file to prevent overwriting without confirmation
    # The check should be for the final intended location (current_folder if moved)
    final_destination_check_path = (
                current_folder / final_output_cbz_name) if is_output_folder_created and final_output_destination_dir != current_folder else (
                final_output_destination_dir / final_output_cbz_name)

    if final_destination_check_path.exists():
        print(
            f"Warning: Output file '{final_output_cbz_name}' already exists in '{final_destination_check_path.parent}'.")
        overwrite = input("Do you want to overwrite it? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Operation cancelled. Existing file not overwritten.")
            sys.exit(0)
        else:
            try:
                if dry_run:
                    print(f"  [DRY RUN] Would delete existing file '{final_output_cbz_name}'")
                else:
                    os.remove(final_destination_check_path)
                    print(f"Existing file '{final_output_cbz_name}' deleted.")
            except OSError as e:
                print(f"Error deleting existing file '{final_output_cbz_name}': {e}. Exiting.", file=sys.stderr)
                sys.exit(1)

    confirm_large_job(files_to_process)

    extracted_subdirs, original_files_to_delete = extract_archives(files_to_process, temp_extraction_root_dir, dry_run=dry_run)

    if not extracted_subdirs and not dry_run:
        print("No archives were successfully extracted. Exiting. 😔")
        # Ensure cleanup runs even if no successful extractions
        cleanup(original_files_to_delete, temp_extraction_root_dir, final_output_destination_dir, current_folder,
                is_output_folder_created, dry_run=dry_run)
        sys.exit(0)

    if create_merged_archive(temp_extraction_root_dir, final_output_cbz_name, final_output_destination_dir,
                             current_folder, is_output_folder_created, dry_run=dry_run):
        cleanup(original_files_to_delete, temp_extraction_root_dir, final_output_destination_dir, current_folder,
                is_output_folder_created, dry_run=dry_run)
        print(f"\n--- Script finished! Successfully created '{final_output_cbz_name}'. Enjoy your comic! 🎉 ---")
    else:
        print("\n--- Script finished with errors during compression. Cleanup might be incomplete. ⚠️ ---")
        # Attempt cleanup of extracted dirs even if compression failed
        cleanup(original_files_to_delete, temp_extraction_root_dir, final_output_destination_dir, current_folder,
                is_output_folder_created, dry_run=dry_run)


if __name__ == "__main__":
    main()
