#!/usr/bin/env python3
"""
MUD Inventory Manager - Main entry point
Scans multiple character inventories on Realms of Despair MUD
"""

import asyncio
import csv
import logging
import argparse
import sys
import time
import signal
import threading
from pathlib import Path
from typing import List, Tuple, Dict

from mud_client import MUDClient
from inventory_scanner import InventoryScanner
from data_manager import DataManager
from config import (
    CHARACTERS_FILE, LOG_FILE, RATE_LIMIT_DELAY,
    MAX_RETRIES, RETRY_DELAY, DEBUG_MODE
)

# Optional Google Sheets support
try:
    from sheets_exporter import SheetsExporter
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global pause control
scan_paused = False
scan_cancelled = False

def toggle_pause():
    """Toggle pause state when user presses a key."""
    global scan_paused
    scan_paused = not scan_paused
    status = "PAUSED" if scan_paused else "RESUMED"
    print(f"\n>>> Scan {status}. Press 'p' to toggle pause, 'q' to quit safely <<<")

def cancel_scan():
    """Cancel the scan gracefully."""
    global scan_cancelled
    scan_cancelled = True
    print(f"\n>>> Scan CANCELLED. Will complete current character then exit safely <<<")

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    global scan_cancelled
    scan_cancelled = True
    print(f"\n>>> Ctrl+C detected. Will complete current character then exit safely <<<")

def setup_keyboard_handler():
    """Setup keyboard input handler in a separate thread."""
    def keyboard_input():
        while not scan_cancelled:
            try:
                key = input().strip().lower()
                if key == 'p':
                    toggle_pause()
                elif key == 'q':
                    cancel_scan()
                    break
            except (EOFError, KeyboardInterrupt):
                cancel_scan()
                break
    
    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    thread = threading.Thread(target=keyboard_input, daemon=True)
    thread.start()
    return thread


def load_characters(filename: str) -> List[Tuple[str, str]]:
    """Load character credentials from CSV file."""
    characters = []
    
    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'username' in row and 'password' in row:
                    characters.append((row['username'], row['password']))
                else:
                    logger.warning(f"Invalid row in CSV: {row}")
                    
        logger.info(f"Loaded {len(characters)} characters from {filename}")
        return characters
        
    except FileNotFoundError:
        logger.error(f"Characters file not found: {filename}")
        logger.info("Please create a characters.csv file with columns: username,password")
        return []
    except Exception as e:
        logger.error(f"Error loading characters: {str(e)}")
        return []


def filter_characters_by_names(characters: List[Tuple[str, str]], names: List[str]) -> List[Tuple[str, str]]:
    """Filter characters by specific names."""
    # Convert names to lowercase for case-insensitive matching
    target_names = [name.lower().strip() for name in names]
    filtered = []
    
    for username, password in characters:
        if username.lower() in target_names:
            filtered.append((username, password))
    
    # Report any names not found
    found_names = [username.lower() for username, _ in filtered]
    not_found = [name for name in target_names if name not in found_names]
    if not_found:
        logger.warning(f"Characters not found: {', '.join(not_found)}")
    
    return filtered


def filter_characters_by_class(characters: List[Tuple[str, str]], char_class: str) -> List[Tuple[str, str]]:
    """Filter characters by class using existing character stats."""
    from data_manager import DataManager
    
    # Load existing character stats
    data_manager = DataManager(load_existing=True)
    
    # Get characters of the specified class
    filtered = []
    class_lower = char_class.lower()
    
    for username, password in characters:
        # Check if we have stats for this character
        for stats in data_manager.character_stats:
            if stats.get('character', '').lower() == username.lower():
                if stats.get('class', '').lower() == class_lower:
                    filtered.append((username, password))
                break
    
    return filtered


def filter_characters_by_range(characters: List[Tuple[str, str]], range_str: str) -> List[Tuple[str, str]]:
    """Filter characters by line number range (1-indexed)."""
    try:
        if '-' in range_str:
            start, end = map(int, range_str.split('-'))
            # Convert to 0-indexed and ensure valid range
            start = max(0, start - 1)
            end = min(len(characters), end)
            return characters[start:end]
        else:
            # Single number
            index = int(range_str) - 1
            if 0 <= index < len(characters):
                return [characters[index]]
            else:
                logger.error(f"Character index {range_str} out of range (1-{len(characters)})")
                return []
    except ValueError:
        logger.error(f"Invalid range format: {range_str}")
        return []


def load_character_groups(filename: str = "groups.csv") -> Dict[str, List[str]]:
    """Load character groups from CSV file."""
    groups = {}
    
    if not Path(filename).exists():
        return groups
    
    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                group_name = row.get('group', '').strip()
                characters = row.get('characters', '').strip()
                
                if group_name and characters:
                    # Split by comma and clean up names
                    char_list = [name.strip() for name in characters.split(',') if name.strip()]
                    groups[group_name.lower()] = char_list
                    
        logger.info(f"Loaded {len(groups)} character groups")
        return groups
        
    except Exception as e:
        logger.warning(f"Could not load groups file: {e}")
        return groups


def filter_characters_by_group(characters: List[Tuple[str, str]], group_name: str) -> List[Tuple[str, str]]:
    """Filter characters by predefined group."""
    groups = load_character_groups()
    
    group_lower = group_name.lower()
    if group_lower not in groups:
        logger.error(f"Group '{group_name}' not found. Available groups: {', '.join(groups.keys())}")
        return []
    
    # Get character names in the group
    group_chars = groups[group_lower]
    return filter_characters_by_names(characters, group_chars)


async def scan_character(username: str, password: str, data_manager: DataManager) -> Tuple[bool, float]:
    """Scan a single character's inventory."""
    start_time = time.time()
    logger.info(f"Processing character: {username}")
    
    for attempt in range(MAX_RETRIES):
        try:
            # Create new client for each character
            client = MUDClient()
            scanner = InventoryScanner(client)
            
            # Connect to MUD
            if not await client.connect():
                logger.error(f"Failed to connect for {username}")
                await asyncio.sleep(RETRY_DELAY)
                continue
                
            # Login
            if not await client.login(username, password):
                logger.error(f"Failed to login as {username}")
                await client.disconnect()
                await asyncio.sleep(RETRY_DELAY)
                continue
                
            # Scan inventory
            scan_result = await scanner.scan_character_inventory(username)
            
            # Handle different return formats (tuple for character only, list for character + house)
            total_items = 0
            if isinstance(scan_result, list):
                # Multiple datasets (character + house)
                for items, char_stats in scan_result:
                    data_manager.add_character_data(items, char_stats)
                    total_items += len(items)
                    logger.info(f"Added {len(items)} items for: {char_stats['character']}")
            else:
                # Single dataset (character only)
                items, char_stats = scan_result
                data_manager.add_character_data(items, char_stats)
                total_items = len(items)
            
            # Logout and disconnect
            await client.logout()
            await client.disconnect()
            
            scan_time = time.time() - start_time
            logger.info(f"Successfully scanned {username}: {total_items} items in {scan_time:.1f}s")
            return True, scan_time
            
        except Exception as e:
            logger.error(f"Error scanning {username}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying... (attempt {attempt + 2}/{MAX_RETRIES})")
                await asyncio.sleep(RETRY_DELAY)
            
    scan_time = time.time() - start_time
    logger.error(f"Failed to scan {username} after {MAX_RETRIES} attempts in {scan_time:.1f}s")
    return False, scan_time


async def main(args):
    """Main execution function."""
    total_start_time = time.time()
    logger.info("=== MUD Inventory Manager Starting ===")
    
    # Load all characters
    all_characters = load_characters(args.characters)
    if not all_characters:
        logger.error("No characters to process")
        return 1
    
    # Handle --list option
    if args.list:
        print("\n=== Available Characters ===")
        for i, (username, _) in enumerate(all_characters, 1):
            print(f"{i:3d}. {username}")
        print(f"\nTotal: {len(all_characters)} characters")
        return 0
    
    # Apply filters based on command-line options
    characters = all_characters
    
    if args.single:
        # Single character or comma-separated list
        names = [name.strip() for name in args.single.split(',')]
        characters = filter_characters_by_names(all_characters, names)
        logger.info(f"Scanning specific characters: {', '.join(names)}")
        
    elif args.group:
        # Predefined group
        characters = filter_characters_by_group(all_characters, args.group)
        logger.info(f"Scanning group: {args.group}")
        
    elif args.char_class:
        # Filter by class
        characters = filter_characters_by_class(all_characters, args.char_class)
        logger.info(f"Scanning all {args.char_class} characters")
        
    elif args.range:
        # Range of characters
        characters = filter_characters_by_range(all_characters, args.range)
        logger.info(f"Scanning range: {args.range}")
    
    if not characters:
        logger.error("No characters match the specified criteria")
        return 1
    
    # Show what will be scanned
    print(f"\n=== Characters to Scan ({len(characters)}) ===")
    for username, _ in characters:
        print(f"  • {username}")
    print()
        
    # Initialize data manager
    data_manager = DataManager()
    
    # Setup keyboard handler for pause/cancel
    print("\n>>> Scan starting. Press 'p' to pause/resume, 'q' to quit safely <<<")
    keyboard_thread = setup_keyboard_handler()
    
    # Process each character
    success_count = 0
    failed_characters = []  # Track failed characters with reasons
    character_times = []
    for i, (username, password) in enumerate(characters):
        # Check for cancellation
        if scan_cancelled:
            logger.info("Scan cancelled by user")
            break
            
        # Handle pause
        while scan_paused and not scan_cancelled:
            await asyncio.sleep(0.5)
            
        if scan_cancelled:
            logger.info("Scan cancelled by user")
            break
            
        if i > 0:
            logger.info(f"Waiting {RATE_LIMIT_DELAY} seconds before next character...")
            # Allow pause/cancel during rate limit delay
            for _ in range(int(RATE_LIMIT_DELAY * 2)):  # Check every 0.5 seconds
                if scan_cancelled:
                    break
                while scan_paused and not scan_cancelled:
                    await asyncio.sleep(0.5)
                if scan_cancelled:
                    break
                await asyncio.sleep(0.5)
            
        if scan_cancelled:
            break
            
        logger.info(f"Processing character {i+1}/{len(characters)}: {username}")
        try:
            success, scan_time = await scan_character(username, password, data_manager)
            character_times.append(scan_time)
            if success:
                success_count += 1
            else:
                # Track failed character with password for review
                failed_characters.append({
                    'username': username,
                    'password': password,
                    'scan_time': scan_time
                })
                logger.warning(f"FAILED: {username} (password: {password}) - scan time: {scan_time:.1f}s")
        except KeyboardInterrupt:
            logger.info("Character scan cancelled by user")
            break
            
    logger.info(f"Scanning complete: {success_count}/{len(characters)} successful")
    
    # Export to CSV
    if success_count > 0:
        csv_file = data_manager.export_to_csv()
        if csv_file:
            logger.info(f"Data exported to: {csv_file}")
            
        # Export character stats
        stats_file = data_manager.export_character_stats()
        if stats_file:
            logger.info(f"Character stats exported to: {stats_file}")
            
        # Export to Google Sheets if requested
        if args.sheets:
            if not SHEETS_AVAILABLE:
                logger.error("❌ Google Sheets export requested but sheets_exporter module not available")
                logger.info("To enable Google Sheets support, ensure sheets_exporter.py is present")
            else:
                logger.info("Exporting to Google Sheets...")
                exporter = SheetsExporter()
                
                if exporter.setup_sheets_client():
                    if exporter.create_or_update_sheet(args.sheet_name):
                        df = data_manager.process_inventory_data()
                        if exporter.upload_inventory_data(df):
                            stats = data_manager.generate_summary_stats()
                            exporter.create_summary_worksheet(stats)
                            
                            url = exporter.get_spreadsheet_url()
                            logger.info(f"Google Sheets updated: {url}")
                        else:
                            logger.error("Failed to upload data to Google Sheets")
                    else:
                        logger.error("Failed to create/update spreadsheet")
                else:
                    logger.error("Failed to authenticate with Google Sheets")
                
        # Print summary
        stats = data_manager.generate_summary_stats()
        print("\n=== Scan Summary ===")
        total_time = time.time() - total_start_time
        avg_time = sum(character_times) / len(character_times) if character_times else 0
        
        print(f"Total Items: {stats['total_items']}")
        print(f"Total Quantity: {stats['total_quantity']}")
        print(f"Unique Items: {stats['unique_items']}")
        print(f"Characters Scanned: {stats['total_characters']}")
        print(f"\n=== Timing Stats ===")
        print(f"Total Scan Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"Average Time per Character: {avg_time:.1f} seconds")
        if len(characters) > success_count:
            estimated_time = avg_time * len(characters)
            print(f"Estimated Time for All Characters: {estimated_time:.1f} seconds ({estimated_time/60:.1f} minutes)")
        
        # Report failed characters for password review
        if failed_characters:
            print(f"\n=== FAILED CHARACTERS ({len(failed_characters)}) ===")
            print("The following characters failed to login - please review passwords:")
            for failed in failed_characters:
                print(f"  {failed['username']} (password: {failed['password']}) - failed in {failed['scan_time']:.1f}s")
            print("\nPossible reasons:")
            print("  • Incorrect password")
            print("  • Character doesn't exist")
            print("  • Character is already logged in")
            print("  • Server connection issues")
        else:
            print(f"\n✅ All {success_count} characters scanned successfully!")
        
        if args.search:
            print(f"\n=== Search Results for '{args.search}' ===")
            results = data_manager.find_items(args.search)
            if not results.empty:
                print(results[['character', 'location', 'item_name', 'quantity']].to_string())
            else:
                print("No items found matching search term")
                
    return 0


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='MUD Inventory Manager - Scan character inventories',
        epilog='Examples:\n'
               '  python main.py --single Kaan              # Scan only Kaan\n'
               '  python main.py --single "Kaan,Malfian"    # Scan Kaan and Malfian\n'
               '  python main.py --group warriors            # Scan all warriors\n'
               '  python main.py --class Warrior             # Scan all Warriors\n'
               '  python main.py                             # Scan all characters',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # File options
    parser.add_argument(
        '--characters',
        default=CHARACTERS_FILE,
        help='CSV file with character credentials (default: characters.csv)'
    )
    
    # Scanning options - mutually exclusive
    scan_group = parser.add_mutually_exclusive_group()
    scan_group.add_argument(
        '--single',
        help='Scan single character or comma-separated list (e.g., "Kaan" or "Kaan,Malfian")'
    )
    scan_group.add_argument(
        '--group',
        help='Scan predefined group from groups.csv'
    )
    scan_group.add_argument(
        '--class',
        dest='char_class',
        help='Scan all characters of a specific class (e.g., Warrior, Cleric)'
    )
    scan_group.add_argument(
        '--range',
        help='Scan range of characters by line number (e.g., "1-5" or "10-20")'
    )
    
    # Export options
    parser.add_argument(
        '--sheets',
        action='store_true',
        help='Export to Google Sheets'
    )
    parser.add_argument(
        '--sheet-name',
        help='Google Sheets name (default: from config)'
    )
    
    # Other options
    parser.add_argument(
        '--search',
        help='Search for items containing this term after scan'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available characters without scanning'
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Parse arguments
    args = parse_arguments()
    
    # Override debug mode if specified
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Run the main async function
    try:
        sys.exit(asyncio.run(main(args)))
    except KeyboardInterrupt:
        logger.info("Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)