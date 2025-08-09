# 🏠 House Mapping Guide

## Overview

Malfian's Vault now supports **super simple house setup**! No more complex CSV editing or technical configurations. Just describe your house in plain English and let the converter do the work.

## Two Ways to Set Up Your House

### 🚀 Option 1: Simple Text File (Recommended)

Create a text file with your house info and use our converter.

#### Step 1: Create House Description File

Create `my_house.txt` (or any `.txt` file) with this format:

```
HOUSE SETUP FOR: YourCharacterName

MY HOUSE NAME: Your House Name

ROOMS IN MY HOUSE:
1. Room Name (description) - has: container1, container2
2. Another Room (how to get here) - has: chest, bag
3. Third Room (navigation description) - has: vault, safe

HOW TO GET TO EACH ROOM:
- Room Name: starting room
- Another Room: from Room Name, go north
- Third Room: from Another Room, go up, then east
```

#### Step 2: Convert to System Format

Run the converter to automatically generate the technical files:

```bash
python house_converter.py my_house.txt
```

The converter will:
- Parse your plain English description
- Generate the proper `houses_v2.csv` format
- Create the technical room configuration
- Make your house ready for scanning

### 🎯 Option 2: Direct CSV Edit (Advanced)

If you prefer working with CSV directly, edit `houses_v2.csv`:

```csv
character,house_name,rooms
YourName,Your House Name,"Room1:path1:container1,container2|Room2:path2:container3,container4"
```

**Path formats:**
- `` (empty) = starting room
- `n` = north
- `u;n;e` = up, then north, then east

## Real Examples

### Example 1: Simple House
```
HOUSE SETUP FOR: Malfian

MY HOUSE NAME: Malfian's Cottage

ROOMS IN MY HOUSE:
1. Living Room (cozy entrance) - has: chest, cabinet
2. Kitchen (cooking area) - has: cupboard, pantry
3. Bedroom (upstairs) - has: wardrobe, dresser

HOW TO GET TO EACH ROOM:
- Living Room: starting room
- Kitchen: from Living Room, go north
- Bedroom: from Living Room, go up
```

### Example 2: Complex Multi-Level House
```
HOUSE SETUP FOR: Kaan

MY HOUSE NAME: Kaan's Manse

ROOMS IN MY HOUSE:
1. Manse of the Macabre (entrance hall) - has: reliquary, crate, shell
2. Madness Below (basement level) - has: shell
3. Base of the Pit (deep basement) - has: crate, reliquary, shell
4. Alchemy Laboratory (east wing) - has: shelf, rack, desk
5. Vault of the Elders (west wing) - has: bin, box

HOW TO GET TO EACH ROOM:
- Manse of the Macabre: starting room
- Madness Below: from Manse of the Macabre, go down
- Base of the Pit: from Madness Below, go down
- Alchemy Laboratory: from Base of the Pit, go south
- Vault of the Elders: from Base of the Pit, go north
```

## Navigation Instructions

### Direction Commands
Use these direction words in your descriptions:
- **Basic**: `north`, `south`, `east`, `west`, `up`, `down`
- **Diagonal**: `northeast`, `northwest`, `southeast`, `southwest`
- **Shortcuts**: `n`, `s`, `e`, `w`, `u`, `d`, `ne`, `nw`, `se`, `sw`

### Multi-Step Paths
For complex navigation, chain directions with "then":
- `"from Room A, go up, then north, then east"`
- `"from Main Hall, go down, then south"`

### Common Container Names
The system recognizes these container types:
- **Storage**: chest, vault, safe, strongbox, box, crate, barrel
- **Bags**: bag, sack, pouch, pack
- **Furniture**: cabinet, cupboard, wardrobe, dresser, shelf, rack, desk, table
- **Special**: reliquary, bin, basket, shell

## Technical Details (Advanced)

### Generated CSV Format
The converter creates entries like:
```csv
character,house_name,rooms
Kaan,Kaan's Manse,"Manse of the Macabre::reliquary,crate,shell|Madness Below:d:shell|Base of the Pit:d;d:crate,reliquary,shell|Alchemy Laboratory:d;d;s:shelf,rack,desk|Vault of the Elders:d;d;n:bin,box"
```

### Path Resolution Algorithm
1. **Starting Room**: Empty path (`""` or `"start"`)
2. **Simple Paths**: Single direction (`"n"`, `"up"`)  
3. **Complex Paths**: Semicolon-separated (`"u;n;e"` = up, then north, then east)

### Room Format: `name:path:containers`
- **name**: Exact room name as shown in MUD
- **path**: Navigation commands from starting room
- **containers**: Comma-separated list of storage items

## Troubleshooting

### Common Issues

**"Can't find room"**: 
- Check room name matches exactly what you see in MUD
- Ensure path directions are correct

**"Container not found"**:
- Verify container names match what's in the room
- Use `look` in-game to see all containers

**"Navigation failed"**:
- Test your directions manually in-game
- Make sure all path steps work from the entrance

### Testing Your Setup

1. **Manual Test**: Follow your directions in-game to verify they work
2. **Dry Run**: Use `python house_converter.py --dry-run my_house.txt` to validate
3. **Scan Test**: Run a house scan to see if navigation works

## Getting Help

### Need Assistance?
- 📖 **Quick Start**: See `SIMPLE_HOUSE_SETUP.md`
- 🐛 **Bug Reports**: Create GitHub issue
- 💬 **Questions**: Message the developers

### Have Us Set It Up
Email us your house description and we'll configure it for you:

```
Hi! Please set up my house:

Character: YourName
House: Your House Name

Rooms:
- Room 1 (entrance): chest, bag
- Room 2 (north): vault, safe
- Room 3 (up from room 2): cabinet

Thanks!
```

We'll send you back the ready-to-use configuration files! 📧

---

**Remember**: The new system handles all the technical complexity for you. Just describe your house in plain English and let the converter do the rest! 🎉