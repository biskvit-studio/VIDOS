# VIDOS - Media Downloader

VIDOS is a professional, modern, and high-performance video and playlist downloader built using **Python**, **Flet** (Flutter-based desktop UI framework), and **yt-dlp**. Designed with a clean Shadcn-inspired dark aesthetic, it features concurrent segment downloads, network performance optimizations, and automatic dependency resolving.

---

## Key Features

- **High-Quality Downloads:** Select custom video qualities up to 1080p (MP4) or extract audio directly to MP3/M4A.
- **Playlist Handling:** Analyze full playlists, select/deselect specific tracks, and download sequentially into clean subfolders.
- **Performance Optimized:**
  - Concurrent fragment downloads (4 simultaneous streams).
  - Configured socket buffer sizes (1MB) and HTTP chunk sizes (10MB) for faster downloads.
  - Multi-stream aware progress tracking with UI throttle limiting (4 Hz max) to prevent UI thread blocking.
- **FFmpeg Auto-detection:** Automatic resolution fallback utilizing both system PATH and bundled `imageio-ffmpeg` package binaries (no manual installation required).
- **Modern UI/UX:** Responsive layout featuring smooth micro-animations, theme toggles, folder explorer navigation, and a persistent JSON configuration system.

---

## Repository & Project Architecture

The project is structured according to clean MVC principles:

```text
Vid Downloader/
├── assets/                  # Graphics, application icons, and custom fonts
│   ├── fonts/               # Montserrat and Unbounded fonts
│   └── vidos_icon.ico       # Desktop app icon
├── downloader/              # Downloader package (core business logic)
│   ├── __init__.py          # Exposed package API
│   ├── config.py            # Local JSON settings persistence
│   ├── engine.py            # Async-wrapped yt-dlp downloader engine
│   └── ffmpeg.py            # Dynamic FFmpeg resolver
├── ui/                      # Flet interface package (views & styling)
│   ├── __init__.py
│   ├── layout.py            # Application sidebar shell layout
│   ├── theme.py             # Shadcn-inspired palette design tokens
│   ├── components/          # Reusable customized components
│   │   ├── buttons.py       # Custom buttons and input fields
│   │   ├── cards.py         # Metadata presentation cards
│   │   └── progress.py      # Multi-metric progress bars & badges
│   └── views/               # Screen modules
│       ├── download_view.py # Parse, analyze, and monitor active downloads
│       ├── history_view.py  # Log of previously downloaded items
│       └── settings_view.py # Directory and requirement management
├── tools/                   # Helper scripts
│   └── font_replacer.py     # Font mass-replacer script
├── main.py                  # Application entry point
├── requirements.txt         # Pinned python dependencies
├── build_app.ps1            # Standalone build PowerShell script
└── LICENSE                  # MIT License
```

---

## Installation & Setup

### 1. Prerequisites
- **Python 3.10 or higher** installed on your system.
- *(Optional)* **FFmpeg** installed on your system PATH. If missing, the application will automatically fall back to the bundled portable version provided by `imageio-ffmpeg`.

### 2. Setup Virtual Environment
Clone the repository and navigate to the project root directory, then run:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
Install all required libraries using pip:

```bash
pip install -r requirements.txt
```

---

## Running the Application

To launch the GUI desktop app, make sure your virtual environment is active and run:

```bash
python main.py
```

---

## Packaging Standalone Executables

A PowerShell build script is provided to compile the application into a single standalone `.exe` using PyInstaller and Flet's pack tool:

```powershell
# Run the build script
.\build_app.ps1
```

Once compilation completes, the packaged executable will be generated inside the `dist/` directory.

---

## License

This project is licensed under the [MIT License](LICENSE).
