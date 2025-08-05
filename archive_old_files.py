#!/usr/bin/env python3
"""Archive old problematic data files and keep only clean versions."""

import os
import glob
import shutil
from datetime import datetime
from pathlib import Path

def archive_old_files():
    """Archive all old data files except the clean ones."""
    
    print("=== Archiving Old Data Files ===\n")
    
    # Create archive directory
    archive_dir = Path("archive")
    archive_dir.mkdir(exist_ok=True)
    
    # Get all data files
    all_files = glob.glob("inventory_backup_*.csv") + glob.glob("character_stats_*.csv")
    
    # Files to keep (only the latest clean versions)
    keep_files = [
        "inventory_backup_CLEAN_20250804_121040.csv",
        "character_stats_CLEAN_20250804_121040.csv"
    ]
    
    # Archive all other files
    archived_count = 0
    for file in all_files:
        if file not in keep_files:
            try:
                # Move to archive directory
                archive_path = archive_dir / file
                shutil.move(file, archive_path)
                archived_count += 1
                print(f"Archived: {file}")
            except Exception as e:
                print(f"Error archiving {file}: {e}")
    
    print(f"\nArchived {archived_count} files")
    print(f"Kept {len(keep_files)} clean files:")
    for file in keep_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✓ {file} ({size:,} bytes)")
        else:
            print(f"  ✗ {file} (missing!)")
    
    # Verify the clean files don't have duplicates
    print(f"\nVerifying clean files...")
    try:
        import pandas as pd
        from collections import defaultdict
        
        # Check inventory file
        inv_file = "inventory_backup_CLEAN_20250804_121040.csv"
        if os.path.exists(inv_file):
            df = pd.read_csv(inv_file)
            chars = df['character'].unique()
            
            # Check for case duplicates
            case_groups = defaultdict(list)
            for char in chars:
                case_groups[char.lower()].append(char)
            
            duplicates = {k: v for k, v in case_groups.items() if len(v) > 1}
            
            print(f"  Inventory: {len(chars)} character names, {len(duplicates)} with case issues")
            if duplicates:
                print("    WARNING: Still has case duplicates!")
                for k, v in list(duplicates.items())[:3]:
                    print(f"      {k}: {v}")
            else:
                print("    ✓ No case duplicates found")
        
        # Check stats file  
        stats_file = "character_stats_CLEAN_20250804_121040.csv"
        if os.path.exists(stats_file):
            df = pd.read_csv(stats_file)
            print(f"  Stats: {len(df)} characters")
            
            # Check for actual duplicates
            duplicates = df[df.duplicated(subset=['character'], keep=False)]
            if len(duplicates) > 0:
                print(f"    WARNING: {len(duplicates)} duplicate character entries!")
            else:
                print("    ✓ No duplicate characters")
                
    except Exception as e:
        print(f"  Error verifying files: {e}")
    
    print(f"\n✓ File cleanup complete!")
    print(f"Only clean data files remain. Web viewer should now show correct character count.")
    
    return True

if __name__ == "__main__":
    archive_old_files()