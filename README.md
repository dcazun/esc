# ESC(ape)

A desktop wellness application that detects prolonged downward posture—typically caused by doomscrolling or prolonged phone use—and gently nudges users back into healthier habits.

## Why ESC?

Modern workspaces make it easy to unconsciously spend long periods looking down at a phone or slouching at a desk. ESC aims to build healthier posture habits through subtle, non-intrusive interventions instead of disruptive reminders.

## Current Features

- ✅ Dlib-based posture detection
- ✅ Automatic posture monitoring
- ✅ Native desktop nudge window
- ✅ Sound reminders
- ✅ Launch at system startup
- ✅ Persistent settings

## Roadmap

- 🌱 Plant reward system
- 📊 Statistics dashboard
- 💾 SQLite session history
- 👥 Friend system
- ☁️ Cross-device sync

## Tech Stack

- **Frontend:** React + TypeScript
- **Backend:** Rust (Tauri)
- **Computer Vision:** Python, OpenCV, dlib
- **Storage:** Tauri Store (SQLite planned)

## Recommended Development Setup

ESC is currently developed and tested on macOS.

### Prerequisites

- Node.js
- Rust + Cargo
- Python 3
- Tauri prerequisites
- A working webcam

### Install frontend dependencies

```bash
npm install
```

### Run the application

```bash
npm run tauri dev
```

### Build the application

```bash
npm run tauri build
```

## Current Limitations

ESC is still under active development.

The posture detector currently depends on a locally configured Python environment and is not yet bundled into the application. Packaging the detector for standalone installation is planned.