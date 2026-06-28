# 🎬 VIDOS — Video Downloader

A simple desktop app for downloading videos and playlists. Nothing fancy, just works. ✨

![VIDOS Preview](assets/vidos_preview.png)

---

## ✨ What It Does

- 📥 **Download videos** from your favorite sites (YouTube, Vimeo, TikTok, and more)
- 📋 **Download full playlists** — select exactly which tracks you want
- 🎵 **Audio only** — grab just the MP3 or M4A if that's all you need
- 🌍 **Available in 8 languages** — English, German, Russian, French, Spanish, Portuguese, Turkish & Indonesian
- 🌙 **Dark & Light mode** — looks good either way
- 📂 **Choose where to save** your files

---

## 🚀 How to Install & Run (For Normal Users)

You do **not** need to install Python, run commands, or set up any programming environment. Just follow these simple steps:

1. Go to the **[Releases](https://github.com/biskvit-studio/VIDOS/releases)** tab on the right side of this page.
2. Download the latest version (look for the file named `VIDOS-vX.X.X-portable.zip`).
3. **Extract** the downloaded `.zip` file anywhere on your computer (for example, to your Desktop or Downloads folder).
4. Open the extracted folder and double-click **`VIDOS.exe`** to launch the app! 🎉

---

## 💻 For Developers (For Coders)

If you want to run the application from source code, modify the project, or build it yourself:

### 1. Prerequisites
- **Python 3.10 or higher** installed on your system.
- **FFmpeg** installed (optional: the application will automatically fall back to the bundled portable version provided by `imageio-ffmpeg` if missing).

### 2. Quick Setup
Clone the repository, navigate to the project directory, and set up your virtual environment:

```bash
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.venv\Scripts\activate.bat
# On macOS/Linux:
source .venv/bin/activate

# 3. Install required packages
pip install -r requirements.txt
```

### 3. Run the App
With your virtual environment active, run:
```bash
python main.py
```

### 4. Build Standalone Executable
To package the app into a single standalone `.exe` file (like the one in Releases), run the build script in PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File .\build_app.ps1
```
The packaged executable will be generated inside the `dist/` folder.

---

## 🛁 The Story

This app was born at a laundry. Sitting there, waiting for the clothes to dry, with nothing to do — so I built this. What started as a way to kill time turned into a proper little tool I actually use every day.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
