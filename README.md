# ESC(ape)

A desktop wellness application that detects prolonged downward posture (typically caused by doomscrolling or prolonged phone use) and gently nudges users back into healthier habits.

Features:
- Dlib posture detection
- Automatic monintoring
- Native desktop notifications
- Sound reminder
- Runs on startup
- Persistent settings

(WIP)
- Plant reward system
- Statistics dashboard
- SQLite session history
- Friend system
- Cross-device sync

## Recommended Development Setup

ESC is currently developed and tested on macOS.

### Prerequisites

- Node.js
- Rust and Cargo
- Python 3
- Tauri system dependencies
- A working webcam

### Install frontend dependencies

```bash
npm install

ESC is still under active development. The Python detector is not yet bundled with the application, so production builds currently depend on a locally configured detector environment.