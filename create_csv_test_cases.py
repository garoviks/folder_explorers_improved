import os
from pathlib import Path
import shutil

def create_csv_test_environment():
    base_dir = Path("/home/nesha/scripts/test_csv_library")
    if base_dir.exists():
        shutil.rmtree(base_dir)
    
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Define test scenarios based on the CSV analysis
    scenarios = {
        "Blood Squad Seven": [
            "Blood Squad Seven 006 (2025) (Digital) (Zone-Empire).cbr",
            "Blood Squad Seven 007 (2025) (Digital) (Zone-Empire).cbr",
            "Blood Squad Seven 008 (2025) (Digital) (Zone-Empire).cbr",
            "Blood Squad Seven v01 (2025).cbz"  # Volume to skip
        ],
        "Nanami": [
            "Nanami 01 - Theatre of the Wind (2019) (Europe Comics) (digital-Empire).cbr",
            "Nanami 02_-_The_Stranger__2019___Europe_Comics___Digital-Empire_.cbr",
            "Nanami 03_-_The_Invisible_Kingdom__2019___Europe_Comics___Digital-Empire_.cbr",
            "Nanami v01 (2019).cbz" # Volume to skip
        ],
        "Lunch Lady": [
            "Lunch Lady 01 and the Cyborg Substitute.cbz",
            "Lunch Lady 02 and the League of Librarians Lunch Lady #2.cbz",
            "Lunch Lady 03 and the Author Visit Vendetta Lunch Lady #3.cbz",
            "Lunch Lady v01.cbz" # Volume to skip
        ],
        "Minky Woodcock": [
            "Minky Woodcock - The Girl Who Handcuffed Houdini 01 (of 04) (2017) (digital) (dargh-Empire).cbr",
            "Minky Woodcock - The Girl Who Handcuffed Houdini 02 (of 04) (2018) (digital) (dargh-Empire).cbr",
            "Minky Woodcock - The Girl Who Handcuffed Houdini 03 (of 04) (2018) (digital) (dargh-Empire).cbr",
            "Minky Woodcock - The Girl Who Handcuffed Houdini 04 (of 04) (2018) (digital) (dargh-Empire).cbr"
        ],
        "Joann Sfar (Multi-Group Test)": [
            "Little Vampire 01 (2003).cbr",
            "Little Vampire 02 Little Vampire Does Kung Fu 2003.cbr",
            "Vampire Loves (2006).cbz" # Different group
        ],
        "Broken Pieces (Leading Zero and hash)": [
            "Broken Pieces 000 (2011) (2 covers) (digital) (Minutemen-Excelsior).cbz",
            "Broken Pieces 01 (of 05) (2011) (2 covers) (digital) (Minutemen-Excelsior).cbz",
            "Broken Pieces 02 (of 05) (2012) (2 covers) (digital) (Minutemen-Excelsior).cbz"
        ]
    }
    
    for folder, files in scenarios.items():
        folder_path = base_dir / folder
        folder_path.mkdir(exist_ok=True)
        for filename in files:
            (folder_path / filename).touch()
            
    print(f"\n✅ Realistic test environment created at: {base_dir}")
    print("\nTo test, run:")
    print(f"python3 /home/nesha/scripts/action_explorer.py {base_dir}")
    print("\nRecommended tests in browser:")
    print("1. In 'Nanami': Click 'Select All'. Verify all issues are selected but 'Nanami v01' is ignored.")
    print("2. In 'Lunch Lady': Click 'Create CBZ'. Verify it correctly groups as 'Lunch Lady'.")
    print("3. In 'Joann Sfar': Select all files and click 'Create CBZ'. Verify the Orange Warning appears for 'Little Vampire' vs 'Vampire Loves'.")
    print("4. In 'Minky Woodcock': Verify it correctly handles the long title before '01 (of 04)'.")

if __name__ == "__main__":
    create_csv_test_environment()
