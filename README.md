# ◈ HabitTrack

**A free, offline-first daily habit & task tracker — no sign-up, no cloud, no BS.**

Track your habits, manage daily tasks, visualize your progress, and build streaks that actually stick. Your data lives in a single JSON file that you own completely.

[![Live App](https://img.shields.io/badge/🚀_Live_App-habittracker--blond.vercel.app-4ade80?style=for-the-badge)](https://habittracker-blond.vercel.app/)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![No Dependencies](https://img.shields.io/badge/Dependencies-Zero-4ade80?style=for-the-badge)]()

---

## What is HabitTrack?

HabitTrack is a personal productivity tool that helps you track daily habits and tasks across a monthly calendar. You can see exactly which days you completed each habit, add daily task lists, run focus timers, and analyze your consistency through charts — all without an account or internet connection.

It comes in three forms: a browser app, a Windows desktop executable, and a Python script. All three use the same JSON data format so your data works across all of them.

---

## How to Use It

### 1. Add Your Habits
Go to **🎯 My Habits** → click **＋ Habit** → enter a name and an emoji icon. Drag the ▲▼ arrows to reorder. Edit or delete anytime.

### 2. Track Daily Completions
Go to **📅 Monthly Grid** → click any cell to mark a habit as done for that day. A ✓ appears and the cell turns green. Click again to uncheck.

### 3. Manage Daily Tasks
Go to **📋 Weekly Tasks** → click the **+** button on any day card → type a task and press Enter. Click a task to check it off. Hover and click ✕ to delete.

### 4. Analyze Your Progress
The Monthly Grid includes bar charts, line charts, pie charts, and per-habit breakdowns. Filter by daily, weekly, per-habit, or overall stats.

### 5. Set Focus Timers
Click **⏱ Timer** in the top bar for a global countdown timer. On the Habits page, each habit has its own timer button for per-habit sessions with alarms.

---

## Open Source

HabitTrack is fully open source under the MIT license. The entire browser app is a single self-contained HTML file — no build tools, no frameworks, no server. You can read every line, fork it, modify it, and host it yourself.

---

## Access It in the Browser

No download required. Just open the link:

**[https://trackyourhealth-five.vercel.app/](https://trackyourhealth-five.vercel.app/)**

Works on any modern browser on any device — desktop, tablet, or phone. You can also download the HTML file and open it directly from your computer with no internet connection.

---

## Access It on Windows — Download the EXE

For a native desktop experience on Windows, download the prebuilt executable from the Releases page:

1. Go to the [**Releases**](../../releases) page
2. Download `HabitTrack.exe` from the latest release
3. Double-click to run — no installation needed
4. Your data is saved as `trackerdata.json` in the same folder as the EXE

> **Note:** Windows may show a SmartScreen warning since the app is unsigned. Click "More info" → "Run anyway" to proceed.

---

## Get the Python Script

If you prefer to run it directly from source:

**Requirements:** Python 3.7+ with tkinter

```bash
# Clone the repo
git clone https://github.com/yourusername/habittrack.git
cd habittrack

# Run directly — no pip install needed
python habittrack.py
```

**Install tkinter if missing:**

| OS | Command |
|----|---------|
| Ubuntu / Debian | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-tkinter` |
| macOS | `brew install python-tk` |
| Windows | Comes with the standard Python installer |

On first run, if no `trackerdata.json` exists, the app starts fresh with a set of example habits. All your data is saved automatically to `trackerdata.json` in the same directory as the script.

---

## Export, Share & Import Your Data

All your habits, completions, tasks, and settings live in a single JSON file. You own it entirely.

**To save your data:**
Click **💾 Save** in the top bar → choose where to save `trackerdata.json`

**To load data on another device:**
Click **📂 Open** → select your `.json` file → everything loads instantly

**To share with someone:**
Send them your `trackerdata.json` file by email, WhatsApp, Google Drive, USB — anything. They open it in their copy of HabitTrack and see your full history.

**The JSON structure is simple and human-readable:**

```json
{
  "habits": [
    { "id": "h1", "name": "Morning Run", "icon": "🏃" }
  ],
  "completions": {
    "2025-11-01": ["h1", "h2"],
    "2025-11-02": ["h1"]
  },
  "tasks": {
    "2025-11-01": [
      { "id": "t1", "text": "Read 20 pages", "done": true }
    ]
  },
  "vm": 11,
  "vy": 2025
}
```

You can edit this file manually in any text editor. Add habits, pre-fill completions, or merge data from multiple files.

---

## Access Anywhere

| Method | How |
|--------|-----|
| **Browser (any device)** | Visit [https://trackyourhealth-five.vercel.app/](https://trackyourhealth-five.vercel.app/) |
| **Offline browser** | Download the HTML file, open it locally — works with no internet |
| **Windows desktop** | Download `HabitTrack.exe` from Releases |
| **Python / any OS** | Run `python habittrack.py` |
| **Sync across devices** | Save `trackerdata.json` to Google Drive / Dropbox / iCloud and open it on each device |
| **Share with others** | Send the `.json` file — works on any platform |

---

## Manage Your Habits & Tasks

### Habits
- Add unlimited habits with custom names and emoji icons
- Reorder by dragging (web) or using ▲▼ buttons (desktop)
- Edit name or icon anytime without losing history
- Delete a habit — your past completion data is preserved in the JSON

### Tasks
- Add per-day task lists in the Weekly view
- Check off tasks as you complete them
- Each day card shows a donut chart of task completion %
- Tasks are stored by date in your JSON file

### Monthly Grid
- Full month view with a cell for every habit × every day
- Future days are locked (greyed out)
- Bottom rows show daily progress %, done count, and not-done count
- Navigate months with ‹ › arrows or jump to today

### Charts
- **Daily** — bar or line chart of daily completion % across the month
- **Weekly** — average completion per week
- **Per Habit** — side-by-side comparison of all habits
- **Overall** — pie chart of total done vs. remaining

---
