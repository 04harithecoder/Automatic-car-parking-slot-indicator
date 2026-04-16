# 🚗 Automatic Car Parking Slot Indicator

A real-time parking management system that integrates **8086 Assembly Language**, **Python Tkinter**, and **MySQL** into a unified application.

---

## 📌 Overview

This project simulates a smart parking system where:
- The **8086 Assembly backend** (running in DOSBox) handles core parking logic
- The **Python Tkinter GUI** provides a modern interface for vehicle entry/exit
- **MySQL** stores all vehicle records persistently
- A **file bridge (`park.txt`)** synchronizes data between the assembly backend and Python frontend in real time

---

## 🏗️ System Architecture

```
User
 │
 ▼
Python Tkinter GUI (parking_main.py)
 ├── EntryPopup   → collects Owner Name, Phone, Vehicle No
 ├── ExitPopup    → visual slot picker
 └── SlotDetailPopup → shows vehicle record
 │                        │
 ▼                        ▼
MySQL (parking_db)     park.txt (Bridge File)
 └── slots table         ├── AVAILABLE=9
     owner · phone       ├── STATUS=OPEN
     vehno · time        └── CMD=ENTRY|EXIT|QUIT|NONE
                                    │
                                    ▼
                        DOSBox → parking.com (FASM 8086 ASM)
                         ├── Reads CMD from park.txt
                         ├── Prints result to DOSBox screen
                         └── Writes CMD=NONE back to park.txt
```

---

## ✨ Features

- 🔢 **Live slot counter** — reads from `park.txt` every 500ms
- 🗺️ **Colour-coded slot map** — green (free) / red (occupied)
- 📋 **Vehicle entry form** — name, phone, vehicle number
- 🖱️ **Visual exit picker** — click occupied slot to free it
- 🔍 **Slot detail view** — click any slot to see vehicle info
- 💾 **MySQL storage** — all vehicle records stored persistently
- 🔴 **Live status indicator** — pulsing OPEN / FULL dot
- 📝 **Activity log** — timestamped entry/exit history
- 🕐 **Live clock** — real-time date and time display
- 🚀 **Auto-launch** — DOSBox opens automatically on startup

---

## 🧩 5 Modules (8086 Assembly)

| Module | Description | Instructions Used |
|--------|-------------|-------------------|
| Input Detection | Reads CMD field from park.txt | INT 21H / AH=3Fh |
| Counter Management | Tracks available slot count | avail_slots variable |
| Condition Checking | Validates ENTRY/EXIT/QUIT | CMP · JE · JNE |
| Display | Prints messages to DOSBox screen | INT 21H / AH=09h · pnum |
| Control Flow | Continuous polling loop | main_loop · JMP · INT 4Ch |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Assembly Backend | FASM (Flat Assembler) + DOSBox 0.74 |
| Frontend | Python 3.10+ · Tkinter |
| Database | MySQL 8.0+ · mysql-connector-python |
| Bridge | park.txt (plain text file) |
| OS | Windows 10/11 |

---

## 📁 File Structure

```
MCMP PROJECT/
 ├── parking.asm        ← FASM 8086 Assembly source
 ├── parking.com        ← Compiled DOS COM file
 ├── parking_main.py    ← Python Tkinter GUI (main file)
 ├── db_manager.py      ← MySQL operations
 ├── db_config.py       ← DB credentials (fill password!)
 ├── db_setup.py        ← Run once to create DB and table
 └── park.txt           ← Auto-created bridge file
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/auto-car-parking-slot-indicator.git
cd auto-car-parking-slot-indicator
```

### 2. Install Python dependencies
```bash
pip install mysql-connector-python pywin32 pyautogui
```

### 3. Configure database
Open `db_config.py` and fill your MySQL password:
```python
DB_CONFIG = {
    "host"     : "localhost",
    "user"     : "root",
    "password" : "YOUR_PASSWORD_HERE",
    "database" : "parking_db"
}
```

### 4. Create the database
```bash
python db_setup.py
```

### 5. Compile the Assembly file
```bash
FASM parking.asm parking.com
```

### 6. Run the system
```bash
python parking_main.py
```
> DOSBox will launch automatically with `parking.com` running!

---

## 🖥️ Screenshots

> *(Add screenshots of your GUI and DOSBox running side by side here)*

---

## 🔮 Future Enhancements

- IoT sensors (IR / Ultrasonic) for automatic vehicle detection
- Arduino / Raspberry Pi hardware deployment
- License plate recognition using computer vision
- Automated billing system
- Cloud-based remote monitoring via mobile app
- SMS / Email notifications to vehicle owners

---

## 👨‍💻 Author

**Hariharan Vijayan**  
B.Sc Computer Science  
GitHub: [@04harithecoder](https://github.com/04harithecoder)

---

## 📄 License

This project is for educational purposes.
