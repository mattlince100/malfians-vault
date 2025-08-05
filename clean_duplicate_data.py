#!/usr/bin/env python3
"""
Clean up duplicate character data from merged files.
This ensures each character only appears once with their most recent scan data.
"""

import pandas as pd
import glob
import os
from datetime import datetime

def clean_duplicate_data():
    """Remove duplicate character data, keeping only the most recent scan for each character."""
    
    # Find the latest merged files
    inventory_files = glob.glob("inventory_backup_*.csv")
    stats_files = glob.glob("character_stats_*.csv")
    
    if not inventory_files or not stats_files:
        print("No data files found to clean")
        return
    
    # Get the latest files
    latest_inventory = max(inventory_files, key=os.path.getctime)
    latest_stats = max(stats_files, key=os.path.getctime)
    
    print(f"Cleaning inventory data from: {latest_inventory}")
    print(f"Cleaning character stats from: {latest_stats}")
    
    # Load and clean inventory data
    inventory_df = pd.read_csv(latest_inventory)
    original_inventory_count = len(inventory_df)
    
    # Group by character and keep all items (no duplicates within character data)
    # But if we had duplicate scans, this would remove older scan_time entries
    inventory_df['scan_time'] = pd.to_datetime(inventory_df['scan_time'], errors='coerce')
    
    # For each character, keep only the items from their most recent scan
    character_latest_scan = inventory_df.groupby('character')['scan_time'].max().to_dict()
    
    # Filter to keep only items from each character's latest scan
    def is_latest_scan(row):
        char_name = row['character']
        latest_time = character_latest_scan.get(char_name)
        if pd.isna(row['scan_time']) or pd.isna(latest_time):
            return True  # Keep items without timestamps
        return row['scan_time'] >= latest_time
    
    cleaned_inventory = inventory_df[inventory_df.apply(is_latest_scan, axis=1)].copy()
    removed_inventory_items = original_inventory_count - len(cleaned_inventory)
    
    # Load and clean character stats (keep only latest entry per character)
    stats_df = pd.read_csv(latest_stats)
    original_stats_count = len(stats_df)
    
    # Remove duplicate characters, keeping the last occurrence (most recent)
    cleaned_stats = stats_df.drop_duplicates(subset=['character'], keep='last')
    removed_stats_entries = original_stats_count - len(cleaned_stats)
    
    # Create new cleaned files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Export cleaned inventory
    cleaned_inventory_file = f"inventory_backup_{timestamp}.csv"
    export_columns = ['character', 'location', 'item_name', 'quantity', 'scan_time']
    if 'raw_line' in cleaned_inventory.columns:
        export_columns.append('raw_line')
    
    cleaned_inventory[export_columns].to_csv(cleaned_inventory_file, index=False)
    
    # Export cleaned stats
    cleaned_stats_file = f"character_stats_{timestamp}.csv"
    cleaned_stats.to_csv(cleaned_stats_file, index=False)
    
    print(f"\n=== Cleanup Results ===")
    print(f"Inventory items: {original_inventory_count} -> {len(cleaned_inventory)} (removed {removed_inventory_items} duplicates)")
    print(f"Character stats: {original_stats_count} -> {len(cleaned_stats)} (removed {removed_stats_entries} duplicates)")
    print(f"Unique characters: {cleaned_inventory['character'].nunique()}")
    print(f"\nCleaned files created:")
    print(f"  {cleaned_inventory_file}")
    print(f"  {cleaned_stats_file}")
    print(f"\nWeb viewer will now load clean, deduplicated data.")

if __name__ == "__main__":
    clean_duplicate_data()