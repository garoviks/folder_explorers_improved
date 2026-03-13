import os
from pathlib import Path

def create_test_environment():
    test_dir = Path("/home/nesha/scripts/test_comics")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Files for the test case
    test_files = [
        # Set 1: Standard Leading Zeros (Matches "Amazing Spider-Man")
        "Amazing Spider-Man 001 (2022).cbz",
        "Amazing Spider-Man 002 (2022).cbz",
        
        # Set 2: Volume to be skipped (Should be unselectable/auto-skip)
        "Amazing Spider-Man v01 (2022).cbz",
        
        # Set 3: No Leading Zeros (Matches "Simple Series")
        "Simple Series 1.cbz",
        "Simple Series 2.cbz",
        
        # Set 4: Another group (To test the multi-group Warning)
        "Ghost Rider 01.cbr",
        "Ghost Rider 02.cbr",
        
        # Set 5: Complex naming (Matches "Archangel 8")
        "Archangel 8 01 (2020).cbr",
        "Archangel 8 02 (2020).cbr",
    ]
    
    for filename in test_files:
        (test_dir / filename).touch()
        
    print(f"\n✅ Test environment created at: {test_dir}")
    print("\nTo test, run:")
    print(f"python3 /home/nesha/scripts/action_explorer.py {test_dir}")
    print("\nThings to try in the browser:")
    print("1. Click 'Select All' -> Observe 'Amazing Spider-Man v01' stays unchecked.")
    print("2. Click 'Show Selected' -> See the list of tracked files.")
    print("3. Try to select 'Ghost Rider' files along with 'Amazing Spider-Man' -> Click 'Create CBZ' -> See orange warning.")
    print("4. Select only 'Archangel 8' files -> Click 'Create CBZ' -> See it correctly group as 'Archangel 8'.")

if __name__ == "__main__":
    create_test_environment()
