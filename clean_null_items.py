#!/usr/bin/env python3
"""
Utility script to clean null item entries from inventory data.
These are typically character prompts that were mistakenly captured.
"""

import pandas as pd
import glob
import os
from datetime import datetime

def clean_null_items():
    """Find and remove inventory entries with null item_name."""
    
    # Find the latest inventory CSV
    csv_files = glob.glob("inventory_backup_*.csv")
    if not csv_files:
        print("No inventory CSV files found")
        return
    
    latest_file = max(csv_files, key=os.path.getctime)
    print(f"Processing: {latest_file}")
    
    # Load the data
    df = pd.read_csv(latest_file)
    initial_count = len(df)
    
    # Find entries with null/NaN item_name
    null_mask = df['item_name'].isna() | (df['item_name'] == 'null') | (df['item_name'] == '')
    null_items = df[null_mask]
    
    if len(null_items) == 0:
        print("No null item entries found!")
        return
    
    print(f"\nFound {len(null_items)} entries with null/empty item_name:")
    print("-" * 60)
    
    # Show details of null entries
    for idx, row in null_items.iterrows():
        print(f"Character: {row.get('character', 'N/A')}")
        print(f"Location: {row.get('location', 'N/A')}")
        print(f"Raw line: {row.get('raw_line', 'N/A')[:100] if pd.notna(row.get('raw_line')) else 'N/A'}")
        print("-" * 60)
    
    # Ask for confirmation
    response = input(f"\nRemove these {len(null_items)} entries? (y/n): ")
    
    if response.lower() == 'y':
        # Remove null entries
        df_clean = df[~null_mask]
        
        # Save cleaned data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"inventory_backup_{timestamp}_cleaned.csv"
        df_clean.to_csv(output_file, index=False)
        
        print(f"\nCleaned data saved to: {output_file}")
        print(f"Removed {len(null_items)} entries")
        print(f"Remaining entries: {len(df_clean)}")
        
        # Optional: backup original
        backup_file = latest_file.replace('.csv', '_before_clean.csv')
        print(f"\nOriginal backed up to: {backup_file}")
        os.rename(latest_file, backup_file)
        os.rename(output_file, latest_file)
        print(f"Cleaned file renamed to: {latest_file}")
        
    else:
        print("Cleanup cancelled")

if __name__ == "__main__":
    clean_null_items()