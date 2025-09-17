# LAN Media Controller
⚠️ Warning:
ffplay.exe and ffprobe.exe may not be downloaded automatically. If the server does not start, please manually download ffmpeg-release-essentials.zip from Gyan FFmpeg Essentials
 and move ffplay.exe and ffprobe.exe from the bin folder into the trol folder. The server will not function properly without these files.
## Overview
This application allows you to remotely control media playback (images, videos, audio) on a host PC via LAN. Users on the same network can submit files or URLs to be played on the host PC. Media can be played in fullscreen or in background (audio-only), with configurable durations or percentage playback.

All code and dependencies are contained within the `trol` folder, including `ffplay.exe` and `ffprobe.exe`, ensuring it can run on Windows PCs without system-wide installations.

---

## Features

- **Background Server:** Runs without taskbar visibility.
- **LAN QR Code:** On startup, a QR code appears for 5 seconds linking to the web UI.
- **Web UI:**
  - Two drag-drop areas:
    - **Image/Video Box:** Upload images/videos.
      - Slider for images (duration in seconds).
      - Slider for videos (percent of video to play).
      - Buttons: `Media Open` (opens default player), `Submit` (fullscreen/foreground playback).
    - **Audio/Video-as-Audio Box:** Upload audio or video files.
      - Slider for percentage of playback.
      - Buttons: `Media Open` (default player), `Submit` (audio-only, background).
  - **Link Box:** Enter a URL and submit to open on host.
  - **Clear Button:** Stops all media, clears temp files.
- **Host Behavior:**
  - Images show fullscreen for specified duration.
  - Videos play fullscreen for selected percent.
  - Audio/video box plays only audio in background.
  - `trol/link.txt` keeps LAN URL updated.
- **Self-Hiding:** `trol` folder is automatically set to hidden.

---

## Setup

1. Place entire `trol` folder on your Windows PC.
2. Ensure `ffplay.exe` and `ffprobe.exe` are inside `trol`.
3. Run `enter.bat` to start the server. The batch file also ensures `ffplay/ffprobe` are executable and hidden as needed.
4. Access LAN URL via QR code or by opening `link.txt`.

---

## Dependencies

All dependencies are bundled in `trol`:
- Python 3.x (Windows)
- Flask
- Pillow
- qrcode
- ffplay.exe / ffprobe.exe (inside `trol`)

No additional system-wide installation is required if using the provided batch and exe files.

---

## Usage

- Open browser and scan QR code.
- Drag and drop files into respective boxes.
- Use sliders to adjust durations/percentages.
- Submit to play media on host PC.
- Clear button stops all playback and cleans temp files.
- Links submitted open in the host browser.

---

## Notes

- Audio/video box files are always played audio-only in background.
- Image fullscreen is handled via Tkinter to ensure slider duration is respected.
- The application is designed to run on PCs without any installed Python packages, provided `trol` folder is intact.
- Batch files (`enter.bat`, `exit.bat`) handle startup and cleanup.

---

## Security

- The `trol` folder is hidden to prevent accidental modification.
- Only LAN clients can submit media.
- Submitted URLs are opened on host machine only.

---

## Troubleshooting

- If images do not display fullscreen for slider duration, ensure Python is installed and Tkinter is available.
- If FFplay errors occur, check that `ffplay.exe` and `ffprobe.exe` are in the `trol` folder.
- Use `exit.bat` to safely stop all media processes.

