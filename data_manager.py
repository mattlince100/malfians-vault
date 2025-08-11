"""Data management for processing and storing inventory data."""

import csv
import pandas as pd
import logging
import glob
import os
from typing import List, Dict, Tuple
from datetime import datetime
from config import OUTPUT_CSV_FILE, SAVE_RAW_OUTPUT

logger = logging.getLogger(__name__)


class DataManager:
    """Manages inventory data processing and storage."""
    
    def __init__(self, load_existing=True):
        self.all_data: List[Dict] = []
        self.character_stats: List[Dict] = []
        
        if load_existing:
            self._load_existing_data()
    
    def normalize_character_name(self, name: str) -> str:
        """Normalize character name to consistent capitalization."""
        if not name:
            return name
        # Just strip whitespace and preserve original casing
        # Don't use .capitalize() as it can break names like "McBride" or "O'Connor"
        return name.strip()
    
    def _load_existing_data(self):
        """Load existing inventory and character stats data from previous scans."""
        try:
            # Load latest inventory data
            inventory_files = glob.glob("inventory_backup_*.csv")
            if inventory_files:
                # Prioritize cleaned files over merged, then regular files
                clean_files = [f for f in inventory_files if 'CLEAN' in f]
                merged_files = [f for f in inventory_files if 'MERGED' in f and 'CLEAN' not in f]
                regular_files = [f for f in inventory_files if 'MERGED' not in f and 'CLEAN' not in f]
                
                # Prefer latest cleaned file, then merged, then regular
                if clean_files:
                    latest_file = max(clean_files, key=os.path.getctime)
                elif merged_files:
                    latest_file = max(merged_files, key=os.path.getctime)
                elif regular_files:
                    latest_file = max(regular_files, key=os.path.getctime)
                else:
                    latest_file = None
                
                if latest_file:
                    df = pd.read_csv(latest_file)
                    self.all_data = df.to_dict('records')
                    logger.info(f"Loaded {len(self.all_data)} existing inventory items from {latest_file}")
            
            # Load latest character stats data
            stats_files = glob.glob("character_stats_*.csv")
            if stats_files:
                # Prioritize cleaned files over merged, then regular files
                clean_files = [f for f in stats_files if 'CLEAN' in f]
                merged_files = [f for f in stats_files if 'MERGED' in f and 'CLEAN' not in f]
                regular_files = [f for f in stats_files if 'MERGED' not in f and 'CLEAN' not in f]
                
                # Prefer latest cleaned file, then merged, then regular
                if clean_files:
                    latest_file = max(clean_files, key=os.path.getctime)
                elif merged_files:
                    latest_file = max(merged_files, key=os.path.getctime)
                elif regular_files:
                    latest_file = max(regular_files, key=os.path.getctime)
                else:
                    latest_file = None
                
                if latest_file:
                    df = pd.read_csv(latest_file)
                    logger.info(f"CSV file contains {len(df)} character records")
                    
                    # Convert to dict but keep as a dict indexed by character name for deduplication
                    existing_stats = {}
                    duplicate_count = 0
                    
                    for _, row in df.iterrows():
                        char_name = str(row['character']).strip()
                        char_key = char_name.lower()
                        
                        if char_key in existing_stats:
                            duplicate_count += 1
                            logger.warning(f"Duplicate character found in CSV: '{char_name}' (lowercase: '{char_key}')")
                            logger.warning(f"  Existing: {existing_stats[char_key]['character']}")
                            logger.warning(f"  New: {char_name}")
                        
                        existing_stats[char_key] = row
                    
                    self.character_stats = list(existing_stats.values())
                    logger.info(f"Loaded {len(self.character_stats)} unique character stats from {latest_file}")
                    if duplicate_count > 0:
                        logger.warning(f"Found {duplicate_count} duplicate characters that were deduplicated")
        
        except Exception as e:
            logger.warning(f"Could not load existing data: {e}")
            # Continue with empty data if loading fails
    
    def add_character_data(self, character_data: List[Dict], char_stats: Dict = None):
        """Add scanned data from a character to the collection, replacing any existing data for that character."""
        
        if character_data and len(character_data) > 0:
            # Preserve original character name for house characters - don't normalize case for houses
            original_name = character_data[0]['character']
            
            # Safety check: ensure character name doesn't contain ANSI codes (indicates corrupted data)
            import re
            if re.search(r'[\x1b\\].*?m', str(original_name)):
                logger.error(f"Character name contains ANSI codes, data may be corrupted: {repr(original_name)}")
                # Try to extract a clean character name or skip this data
                clean_name = re.sub(r'\x1b\[[0-9;]*m', '', str(original_name))
                clean_name = re.sub(r'\\x1b\[[0-9;]*m', '', clean_name).strip()
                if clean_name and len(clean_name) < 50:  # Reasonable character name length
                    logger.info(f"Recovered character name: {clean_name}")
                    original_name = clean_name
                    # Update all items with clean name
                    for item in character_data:
                        item['character'] = clean_name
                else:
                    logger.error("Cannot recover character name, skipping corrupted data")
                    return
            
            # Only normalize non-house characters
            if '_house' not in original_name.lower() and '_House' not in original_name:
                normalized_name = self.normalize_character_name(original_name)
                for item in character_data:
                    item['character'] = normalized_name
            else:
                # Keep house character names exactly as they are
                normalized_name = original_name
            
            # Get character name for comparison - exact match now, not just case-insensitive
            char_name_exact = normalized_name
            
            # Remove any existing inventory data for this exact character name
            original_count = len(self.all_data)
            self.all_data = [item for item in self.all_data if item['character'] != char_name_exact]
            removed_count = original_count - len(self.all_data)
            
            if removed_count > 0:
                logger.info(f"Removed {removed_count} existing items for character: {normalized_name}")
            
            # Add new inventory data for this character
            self.all_data.extend(character_data)
            logger.info(f"Added {len(character_data)} new items for character: {normalized_name}")
        
        if char_stats:
            original_char_name = char_stats['character']
            
            # Don't normalize house character names - they need exact case matching
            if '_house' in original_char_name.lower() or '_House' in original_char_name:
                normalized_name = original_char_name  # Keep house names exactly as-is
            else:
                normalized_name = self.normalize_character_name(original_char_name)
            
            char_stats['character'] = normalized_name
            char_name = normalized_name.lower()
            
            logger.info(f"Processing character stats: '{original_char_name}' → '{normalized_name}' (key: '{char_name}')")
            logger.info(f"Current character_stats list has {len(self.character_stats)} entries before processing")
            
            # Find and replace existing stats for this character
            existing_index = None
            for i, existing_stats in enumerate(self.character_stats):
                existing_char = existing_stats.get('character', 'UNKNOWN')
                existing_key = str(existing_char).lower()
                if existing_key == char_name:
                    existing_index = i
                    logger.info(f"Found existing stats for '{char_name}' at index {i} (existing char: '{existing_char}')")
                    break
            
            if existing_index is not None:
                # Update existing character stats
                old_char_name = self.character_stats[existing_index].get('character', 'UNKNOWN')
                self.character_stats[existing_index] = char_stats
                logger.info(f"Updated stats: '{old_char_name}' → '{normalized_name}' (total: {len(self.character_stats)})")
            else:
                # Add new character stats
                self.character_stats.append(char_stats)
                logger.info(f"Added new character: '{normalized_name}' (total: {len(self.character_stats)})")
        
        total_items = len(self.all_data)
        total_characters = len(set(item['character'].lower() for item in self.all_data))
        logger.info(f"Dataset now contains {total_items} items from {total_characters} characters")
    
    def export_character_stats(self, filename: str = None) -> str:
        """Export character statistics to CSV file."""
        if not self.character_stats:
            logger.warning("No character stats to export")
            return None
        
        logger.info(f"Exporting {len(self.character_stats)} character stats")
        if self.character_stats:
            first_stat = self.character_stats[0]
            logger.info(f"First character stat keys: {list(first_stat.keys())}")
            logger.info(f"First character name: {first_stat.get('character', 'NOT SET')}")
            
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"character_stats_{timestamp}.csv"
        
        try:
            # Clean character_stats data for CSV export
            clean_stats = []
            for stat in self.character_stats:
                clean_stat = {}
                
                # Convert pandas Series to dict if needed
                if hasattr(stat, 'to_dict'):
                    stat_dict = stat.to_dict()
                elif isinstance(stat, dict):
                    stat_dict = stat
                else:
                    logger.warning(f"Unexpected character stat type: {type(stat)} - skipping")
                    continue
                
                # Clean each field for CSV compatibility
                for key, value in stat_dict.items():
                    if isinstance(value, (dict, list)):
                        clean_stat[key] = str(value)
                    elif key == 'raw_score' and value:
                        # Special handling for raw_score to prevent CSV corruption
                        import re
                        clean_value = str(value)
                        # Strip ANSI codes and replace newlines with spaces
                        clean_value = re.sub(r'\x1b\[[0-9;]*m', '', clean_value)
                        clean_value = re.sub(r'\\x1b\[[0-9;]*m', '', clean_value)
                        clean_value = clean_value.replace('\n', ' ').replace('\r', ' ')
                        # Truncate if too long to prevent CSV issues
                        if len(clean_value) > 1000:
                            clean_value = clean_value[:1000] + '...'
                        clean_stat[key] = clean_value
                    else:
                        # Convert to string and clean any problematic characters
                        clean_value = str(value) if value is not None else ''
                        # Remove any remaining newlines or special chars that could break CSV
                        clean_value = clean_value.replace('\n', ' ').replace('\r', ' ')
                        clean_stat[key] = clean_value
                
                clean_stats.append(clean_stat)
            
            df_stats = pd.DataFrame(clean_stats)
            # Use proper CSV escaping to handle any remaining special characters
            df_stats.to_csv(filename, index=False, escapechar='\\', quoting=1)
            logger.info(f"Exported {len(df_stats)} character stats to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exporting character stats: {str(e)}")
            logger.error(f"Character stats structure: {type(self.character_stats)}")
            if self.character_stats:
                logger.error(f"First stat structure: {type(self.character_stats[0])}")
            return None
        
    def process_inventory_data(self) -> pd.DataFrame:
        """Process raw inventory data into a cleaned DataFrame."""
        if not self.all_data:
            logger.warning("No data to process")
            return pd.DataFrame()
            
        # Create DataFrame
        df = pd.DataFrame(self.all_data)
        
        # Sort by character and location
        df = df.sort_values(['character', 'location', 'item_name'])
        
        # Add additional columns for analysis
        df['is_equipment'] = df['location'].str.startswith('equipped:')
        df['container'] = df['location'].apply(lambda x: x.split(':')[0])
        
        logger.info(f"Processed {len(df)} total items")
        return df
    
    def export_to_csv(self, filename: str = None) -> str:
        """Export inventory data to CSV file."""
        if filename is None:
            filename = OUTPUT_CSV_FILE
            
        df = self.process_inventory_data()
        
        if df.empty:
            logger.warning("No data to export")
            return ""
            
        # Select columns to export - include house-specific columns if they exist
        export_columns = ['character', 'location', 'item_name', 'quantity', 'scan_time']
        if SAVE_RAW_OUTPUT:
            export_columns.append('raw_line')
        
        # Add house-specific columns if they exist in the data
        if 'house_owner' in df.columns:
            export_columns.append('house_owner')
        if 'house_name' in df.columns:
            export_columns.append('house_name')
            
        df[export_columns].to_csv(filename, index=False)
        logger.info(f"Exported {len(df)} items to {filename}")
        
        return filename
    
    def generate_summary_stats(self) -> Dict[str, any]:
        """Generate summary statistics for the inventory data."""
        df = self.process_inventory_data()
        
        if df.empty:
            return {
                'total_items': 0,
                'total_characters': 0,
                'scan_time': datetime.now().isoformat()
            }
            
        # Calculate statistics
        stats = {
            'total_items': len(df),
            'total_quantity': df['quantity'].astype(int).sum(),
            'unique_items': df['item_name'].nunique(),
            'total_characters': df['character'].nunique(),
            'scan_time': datetime.now().isoformat(),
            'character_summary': [],
            'location_summary': []
        }
        
        # Character summary
        char_summary = df.groupby('character').agg({
            'item_name': 'count',
            'quantity': lambda x: x.astype(int).sum()
        }).reset_index()
        char_summary.columns = ['character', 'item_count', 'total_quantity']
        stats['character_summary'] = char_summary.to_dict('records')
        
        # Location summary
        loc_summary = df.groupby('container').agg({
            'item_name': 'count',
            'quantity': lambda x: x.astype(int).sum()
        }).reset_index()
        loc_summary.columns = ['location', 'item_count', 'total_quantity']
        stats['location_summary'] = loc_summary.to_dict('records')
        
        # Most common items
        item_counts = df.groupby('item_name').agg({
            'quantity': lambda x: x.astype(int).sum(),
            'character': 'count'
        }).reset_index()
        item_counts.columns = ['item_name', 'total_quantity', 'character_count']
        item_counts = item_counts.sort_values('total_quantity', ascending=False).head(10)
        stats['top_items'] = item_counts.to_dict('records')
        
        return stats
    
    def find_items(self, search_term: str) -> pd.DataFrame:
        """Search for items matching a term."""
        df = self.process_inventory_data()
        
        if df.empty:
            return pd.DataFrame()
            
        # Case-insensitive search
        mask = df['item_name'].str.contains(search_term, case=False, na=False)
        results = df[mask]
        
        logger.info(f"Found {len(results)} items matching '{search_term}'")
        return results
    
    def get_character_inventory(self, character_name: str) -> pd.DataFrame:
        """Get all items for a specific character."""
        df = self.process_inventory_data()
        
        if df.empty:
            return pd.DataFrame()
            
        return df[df['character'] == character_name]