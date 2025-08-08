# ⚡ Quick Start Guide

Get Malfian's Vault running in **5 minutes**!

## 1. Install (30 seconds)
```bash
pip install -r requirements.txt
```

## 2. Add Your Characters (1 minute)
```bash
cp characters.csv.example characters.csv
# Edit characters.csv - add your character names and passwords
```

## 3. Start Scanning! (30 seconds)
```bash
python main.py
```

That's it! Your characters are now being scanned. 🎉

## 4. View Your Inventory (30 seconds)
While scanning runs, open another terminal:
```bash
python web_viewer.py
```
Go to: http://127.0.0.1:5000

## 5. Add Your House (Optional - 2 minutes)

**Super Easy Method:**
```bash
cp house_example.txt my_house.txt
# Edit my_house.txt - describe your house in plain English
python house_converter.py my_house.txt
```

Add the house character to `characters.csv` and scan again!

## Need Help?

- 📖 **Full guide:** See `README.md`
- 🏠 **House setup:** See `SIMPLE_HOUSE_SETUP.md`  
- 🐛 **Issues:** Create a GitHub issue
- 💬 **Questions:** Message us

**Welcome to Malfian's Vault!** 🏆