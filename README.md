# 🪟 FunctionWin

**Natural language control for Windows — runs 100% locally.**

Created by [Dhyey Kutana](https://github.com/dhyeykutana), taking reference from [FunctionMac](https://github.com/krupagaliya/FunctionMac).

Uses **FunctionGemma** (open weights) with **Ollama** to translate plain English into executable Windows actions — fully on-device. No cloud. No data leaving your machine.

---

## ✨ Features

| Category | Functions |
|---|---|
| 📋 System | Screenshot, Clipboard (copy/paste/get) |
| 🎨 Appearance | Dark/Light theme toggle, Wallpaper |
| 🔊 Audio | Set/Get/Mute/Unmute volume |
| 💡 Display | Set/Get brightness (laptop WMI) |
| 🔕 Focus Assist | Enable/Disable Do Not Disturb |
| 📂 Files | Find files, Open file/folder, Text file processing |
| 📱 Apps | Open/Quit apps, List running apps, List installed apps |
| 📊 System Info | CPU, Memory, Disk, Battery, System specs |
| 🖱️ GUI Automation | Click, Drag, Type, Keyboard shortcuts, Scroll |
| 📅 Productivity | Reminders (toast + Task Scheduler), Notifications |
| 🎵 Media | Play/Pause/Next/Previous/Stop (media keys) |
| 🌐 Network | Wi-Fi scan, Network interfaces |
| 🧮 Data | Math expressions, Statistical analysis, QR codes |
| 🔧 Windows Extras | Lock screen, Empty Recycle Bin |

---

## 🚀 Quick Start

### 1. Prerequisites

- **Windows 10 / 11**
- **Python 3.10+**
- **Ollama** — [download here](https://ollama.com/download/windows)

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Pull the model

```bash
ollama pull functiongemma:270m
```

### 4a. Run the Streamlit web app

```bash
python -m streamlit run streamlit_app.py
```

### 4b. Or use the CLI

```bash
python windows_ai_assistant.py
```

---

## 🗣️ Example Queries

```
Take a screenshot and save it to desktop
Set volume to 60 percent
Switch to dark mode
Show me battery information
Find all PDF files in my Documents folder
What's my CPU usage right now?
Lock the screen
Set brightness to 80%
Play next track
Show running applications
Empty the recycle bin
Get my IP address
```

---

## 🗂️ Project Structure

```
FunctionWin/
├── windows_functions.py      # All Windows function implementations
├── windows_ai_assistant.py   # AI orchestrator (Ollama + FunctionGemma)
├── streamlit_app.py          # Web UI (AI + Direct Functions modes)
├── requirements.txt
└── README.md
```

---

## 🔑 Key Differences from FunctionMac

| FunctionMac (macOS) | FunctionWin (Windows) |
|---|---|
| AppleScript (`osascript`) | PowerShell (`powershell -Command`) |
| `pbcopy` / `pbpaste` | `Set-Clipboard` / `Get-Clipboard` |
| PyXA library | `winreg`, `ctypes`, `pywin32` |
| `screencapture` CLI | `pyautogui.screenshot()` |
| IOKit brightness | WMI `WmiMonitorBrightnessMethods` |
| macOS Focus modes | Windows Focus Assist (registry) |
| `defaults write` (theme) | Registry `AppsUseLightTheme` |
| `ioreg` / `system_profiler` | WMI / `Get-WmiObject` |
| `osascript` calendar/reminders | Task Scheduler + toast notifications |
| Media keys via AppleScript | `ctypes` virtual key codes (0xB0–0xB3) |

---

## ⚠️ Notes

- **Brightness control** works on laptops (WMI). Desktop monitors need physical buttons or [nircmd](https://www.nirsoft.net/utils/nircmd.html).
- **Some functions** (theme, notifications, screen lock) may require running as **Administrator**.
- **pywin32** is optional but recommended for deeper Windows integration.
- Tested on Windows 10 22H2 and Windows 11 23H2.

---

## 📜 Credits

**FunctionWin** created by [Dhyey Kutana](https://github.com/dhyeykutana), taking reference from [FunctionMac](https://github.com/krupagaliya/FunctionMac).
