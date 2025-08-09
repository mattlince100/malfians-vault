# 🏠 Simple House Setup Guide

**Setting up your house is now super easy!** Just follow these simple steps.

## Quick Setup (5 minutes)

### Step 1: Create Your House Description

Create a text file called `my_house.txt` and fill it out like this:

```
HOUSE SETUP FOR: YourCharacterName

MY HOUSE NAME: Your House Name

ROOMS IN MY HOUSE:
1. Room Name (description) - has: container1, container2, container3
2. Another Room (how to get here from room 1) - has: chest, bag
3. Third Room (how to get here) - has: vault, safe

HOW TO GET TO EACH ROOM:
- Room Name: starting room (where you enter the house)
- Another Room: from Room Name, go north
- Third Room: from Another Room, go up, then east
```

### Step 2: Real Example

Here's a real example for Malfian's Tower:

```
HOUSE SETUP FOR: Malfian

MY HOUSE NAME: Malfian's Tower

ROOMS IN MY HOUSE:
1. Main Hall (entrance room) - has: chest, cabinet, vault
2. Storage Room (upstairs) - has: bag, sack, barrel
3. Treasure Room (upper level north) - has: strongbox, safe
4. Workshop (basement east) - has: toolbox, crate

HOW TO GET TO EACH ROOM:
- Main Hall: starting room
- Storage Room: from Main Hall, go up
- Treasure Room: from Storage Room, go up, then north
- Workshop: from Main Hall, go down, then east
```

### Step 3: Let Us Convert It

1. Save your `my_house.txt` file
2. Run: `python house_converter.py my_house.txt`
3. The system automatically creates the technical files
4. Make sure your character is in `characters.csv` 
5. Your house is ready to scan with `--house` flag!

## Super Simple Rules

### ✅ What You Need to Know:
- **Room names**: Just the name you see when you enter
- **Containers**: What storage items are in each room (chest, bag, vault, etc.)
- **Directions**: How to walk from one room to another

### ✅ Directions You Can Use:
- `north`, `south`, `east`, `west`
- `up`, `down` 
- `northeast`, `northwest`, `southeast`, `southwest`

### ✅ Common Containers:
- chest, bag, sack, vault, safe, cabinet
- strongbox, box, barrel, basket, crate
- shelf, rack, desk, table, cupboard

## Even Easier: Email Us!

**Too busy to set this up?** Just email us your house info:

```
Hi! Please set up my house:

Character: YourName
House: Your House Name

I have these rooms:
- Room 1 (entrance): chest, bag
- Room 2 (north of room 1): vault, safe
- Room 3 (up from room 2): cabinet

Thanks!
```

We'll set it up for you and send back the files! 📧

## What Happens Next?

Once your house is set up:

1. **Scanning Works**: The system knows how to navigate your house
2. **Visual Map**: You get a beautiful clickable house map
3. **Room Filtering**: Click rooms to see only those items
4. **Full Colors**: All your house items display with MUD colors

## Need Help?

- 🆘 **Having trouble?** Create an issue on GitHub
- 💬 **Quick question?** Message us 
- 📖 **Want technical details?** See `HOUSE_MAPPING_GUIDE.md`

**Remember: We handle all the technical stuff. You just tell us about your house in plain English!** 🎉