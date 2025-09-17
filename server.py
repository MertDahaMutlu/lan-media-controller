#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FINAL server.py — Tkinter image fullscreen for photos + existing ffplay behavior for video/audio
# Place this file inside the "trol" folder. Recommended: put ffplay.exe & ffprobe.exe in same folder (or in PATH).
# Requirements: pip install -r requirements.txt

import sys
import os
import io
import uuid
import socket
import shutil
import subprocess
from pathlib import Path
from threading import Thread, Lock
from flask import Flask, request, render_template, jsonify
import qrcode
from PIL import Image

# ---------- CLI mode: show image fullscreen (separate process) ----------
# Usage: python server.py --show-image "C:\path\to\img.jpg" 3.5
if len(sys.argv) >= 3 and sys.argv[1] == "--show-image":
    # args: --show-image <path> <seconds>
    img_path = sys.argv[2]
    try:
        secs = float(sys.argv[3]) if len(sys.argv) >= 4 else 1.0
    except Exception:
        secs = 1.0
    try:
        import tkinter as tk
        from PIL import ImageTk, Image as PILImage
        root = tk.Tk()
        root.withdraw()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        # create a fullscreen window
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        # load image and resize preserving aspect
        img = PILImage.open(img_path)
        img_ratio = img.width / img.height
        scr_ratio = screen_w / screen_h
        if img_ratio > scr_ratio:
            new_w = screen_w
            new_h = int(screen_w / img_ratio)
        else:
            new_h = screen_h
            new_w = int(screen_h * img_ratio)
        img_resized = img.resize((new_w, new_h), PILImage.LANCZOS)
        win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.geometry(f"{screen_w}x{screen_h}+0+0")
        win.attributes("-topmost", True)
        # center image
        canvas = tk.Canvas(win, width=screen_w, height=screen_h, highlightthickness=0)
        canvas.pack()
        photo = ImageTk.PhotoImage(img_resized)
        x = (screen_w - new_w) // 2
        y = (screen_h - new_h) // 2
        canvas.create_image(x, y, anchor="nw", image=photo)
        win.update()
        # show then destroy after secs*1000 ms
        win.after(int(max(1, secs) * 1000), lambda: (win.destroy(), root.destroy()))
        root.mainloop()
    except Exception:
        # fallback: try ffplay as last resort
        try:
            ffplay = shutil.which("ffplay") or "ffplay"
            subprocess.Popen([ffplay, "-autoexit", "-fs", "-t", str(secs), img_path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    sys.exit(0)

# ---------- Server mode ----------
# BASE dizin: bu script'in bulunduğu klasör (trol/)
BASE_DIR = Path(__file__).resolve().parent
TROL_DIR = BASE_DIR
UPLOADS = BASE_DIR / "uploads"
UPLOADS.mkdir(exist_ok=True)
LINK_FILE = TROL_DIR / "link.txt"

APP = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))

IS_WINDOWS = os.name == "nt"
DEVNULL = subprocess.DEVNULL
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0

# prefer local ffplay/ffprobe
FFPLAY = str(BASE_DIR / "ffplay.exe") if (BASE_DIR / "ffplay.exe").exists() else shutil.which("ffplay") or "ffplay"
FFPROBE = str(BASE_DIR / "ffprobe.exe") if (BASE_DIR / "ffprobe.exe").exists() else shutil.which("ffprobe") or "ffprobe"

proc_lock = Lock()
spawned_procs = []

def hide_trol_folder():
    if IS_WINDOWS:
        try:
            subprocess.call(["attrib", "+h", str(TROL_DIR)])
        except Exception:
            pass

def write_link_file(url: str):
    try:
        TROL_DIR.mkdir(parents=True, exist_ok=True)
        hide_trol_folder()
        with open(LINK_FILE, "w", encoding="utf-8") as f:
            f.write(url)
    except Exception:
        pass

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def secure_filename(fn: str) -> str:
    return "".join(c for c in fn if c.isalnum() or c in "._- ").strip().replace(" ", "_") or f"file_{uuid.uuid4().hex}"

def spawn_process(cmd, foreground=False):
    """
    Start subprocess and record it.
    foreground=True  -> allow window (used for image/video box submits so media appears on top)
    foreground=False -> hide console (used for audio-only background)
    """
    try:
        flags = 0 if foreground else CREATE_NO_WINDOW
        p = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL, creationflags=flags)
    except Exception:
        try:
            p = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL)
        except Exception:
            return None
    with proc_lock:
        spawned_procs.append(p)
    return p

def stop_all_spawned():
    with proc_lock:
        for p in list(spawned_procs):
            try:
                p.kill()
            except Exception:
                try:
                    p.terminate()
                except Exception:
                    pass
        spawned_procs.clear()
    # extra safety: kill ffplay processes on Windows
    if IS_WINDOWS:
        try:
            subprocess.call(["taskkill", "/IM", "ffplay.exe", "/F"], stdout=DEVNULL, stderr=DEVNULL)
        except Exception:
            pass

def get_duration(path: str):
    try:
        out = subprocess.check_output([FFPROBE, "-v", "error", "-show_entries",
                                       "format=duration", "-of",
                                       "default=noprint_wrappers=1:nokey=1", path],
                                      stderr=subprocess.DEVNULL)
        return float(out.decode().strip())
    except Exception:
        return None

def show_qr_for_startup(url: str):
    try:
        img = qrcode.make(url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        try:
            import tkinter as tk
            from PIL import ImageTk
            root = tk.Tk()
            root.overrideredirect(True)
            w = 360; h = 360
            root.geometry(f"{w}x{h}+50+50")
            root.lift(); root.attributes("-topmost", True)
            photo = ImageTk.PhotoImage(Image.open(buf))
            lbl = tk.Label(root, image=photo)
            lbl.pack()
            root.after(5000, root.destroy)
            root.mainloop()
        except Exception:
            pass
    except Exception:
        pass

@APP.route("/")
def index():
    return render_template("index.html")

@APP.route("/upload", methods=["POST"])
def upload():
    """
    form fields:
      - file (optional when box=link)
      - mode: 'submit' or 'gallery'
      - box: 'image' / 'media' / 'audio' / 'link'
      - image_secs: (1-5)
      - percent: (0-100)
      - url: optional (link to open on host)
    Note: audio/video box (box == 'audio') ALWAYS plays as audio-only on submit (nodisp + background).
    """
    mode = request.form.get("mode", "submit")
    box = request.form.get("box", "image")
    link_to_open = (request.form.get("url") or "").strip()
    try:
        image_secs = float(request.form.get("image_secs", 1.0))
    except Exception:
        image_secs = 1.0
    try:
        percent = int(request.form.get("percent", 100))
    except Exception:
        percent = 100

    f = request.files.get("file")

    # write LAN link (update trol/link.txt and ensure trol hidden)
    ip = get_local_ip()
    url = f"http://{ip}:5000/"
    write_link_file(url)

    # LINK box handling
    if box == "link":
        if link_to_open and mode == "submit":
            try:
                import webbrowser
                webbrowser.open(link_to_open, new=0)
            except Exception:
                pass
            return jsonify(status="link_opened")
        return jsonify(status="no_link"), 400

    if not f:
        return jsonify(status="no_file"), 400

    filename = secure_filename(f.filename or f"file_{uuid.uuid4().hex}")
    save_path = UPLOADS / f"{uuid.uuid4().hex}_{filename}"
    f.save(str(save_path))
    path = str(save_path)

    lower = filename.lower()
    is_image = any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"))
    is_video = any(lower.endswith(ext) for ext in (".mp4", ".mkv", ".mov", ".webm", ".avi"))
    # Treat mp4 in audio-box as audio-only
    is_audio = any(lower.endswith(ext) for ext in (".mp3", ".wav", ".aac", ".ogg", ".flac")) or (lower.endswith(".mp4") and box == "audio")

    # GALLERY: open with host default player (normal player, not frameless)
    if mode == "gallery":
        try:
            if IS_WINDOWS:
                os.startfile(path)
            else:
                if shutil.which("xdg-open"):
                    subprocess.Popen(["xdg-open", path], stdout=DEVNULL, stderr=DEVNULL)
                else:
                    spawn_process([FFPLAY, "-autoexit", "-t", "1", path], foreground=False)
        except Exception:
            spawn_process([FFPLAY, "-autoexit", "-t", "1", path], foreground=False)
        return jsonify(status="gallery_started")

    # SUBMIT: host behavior

    # IMAGE submit -> use a separate Python process that shows fullscreen image via Tkinter
    if is_image and box != "audio":
        secs = max(1.0, min(5.0, image_secs))
        # call this script as separate process with --show-image to ensure correct fullscreen behavior
        cmd = [sys.executable, str(__file__), "--show-image", path, str(secs)]
        # foreground True so it appears on top
        spawn_process(cmd, foreground=True)
        return jsonify(status="submitted_image", secs=secs)

    # VIDEO submitted from media box -> fullscreen, percent-based, foreground
    if is_video and box != "audio":
        duration = get_duration(path) or 0.0
        pct = max(0, min(100, percent))
        if duration > 0:
            play_seconds = max(0.01, duration * (pct / 100.0))
            cmd = [FFPLAY, "-autoexit", "-fs", "-alwaysontop", "-ss", "0", "-t", str(play_seconds), path]
            spawn_process(cmd, foreground=True)
            return jsonify(status="submitted_video", play_seconds=play_seconds, duration=duration)
        else:
            cmd = [FFPLAY, "-autoexit", "-fs", "-alwaysontop", path]
            spawn_process(cmd, foreground=True)
            return jsonify(status="submitted_video_full")

    # AUDIO box submit -> audio-only background (nodisp + foreground=False)
    if is_audio and box == "audio":
        duration = get_duration(path) or 0.0
        pct = max(0, min(100, percent))
        if duration > 0:
            play_seconds = max(0.01, duration * (pct / 100.0))
            cmd = [FFPLAY, "-autoexit", "-nodisp", "-ss", "0", "-t", str(play_seconds), path]
        else:
            cmd = [FFPLAY, "-autoexit", "-nodisp", path]
        spawn_process(cmd, foreground=False)
        return jsonify(status="submitted_audio")

    # If a video file was uploaded to the audio-box ensure audio-only behavior
    if is_video and box == "audio":
        duration = get_duration(path) or 0.0
        pct = max(0, min(100, percent))
        if duration > 0:
            play_seconds = max(0.01, duration * (pct / 100.0))
            cmd = [FFPLAY, "-autoexit", "-nodisp", "-ss", "0", "-t", str(play_seconds), path]
        else:
            cmd = [FFPLAY, "-autoexit", "-nodisp", path]
        spawn_process(cmd, foreground=False)
        return jsonify(status="submitted_video_as_audio")

    # AUDIO file submitted from media box - treat as audio-only background
    if is_audio and box != "audio":
        duration = get_duration(path) or 0.0
        pct = max(0, min(100, percent))
        if duration > 0:
            play_seconds = max(0.01, duration * (pct / 100.0))
            cmd = [FFPLAY, "-autoexit", "-nodisp", "-ss", "0", "-t", str(play_seconds), path]
        else:
            cmd = [FFPLAY, "-autoexit", "-nodisp", path]
        spawn_process(cmd, foreground=False)
        return jsonify(status="submitted_audio_from_media_box")

    # Fallback
    spawn_process([FFPLAY, "-autoexit", "-t", "1", path], foreground=False)
    return jsonify(status="submitted_fallback")

@APP.route("/clear", methods=["POST"])
def clear():
    stop_all_spawned()
    try:
        for f in UPLOADS.glob("*"):
            try:
                f.unlink()
            except Exception:
                pass
    except Exception:
        pass
    return jsonify(status="cleared")

def start():
    ip = get_local_ip()
    url = f"http://{ip}:5000/"
    write_link_file(url)
    Thread(target=show_qr_for_startup, args=(url,), daemon=True).start()
    APP.run(host="0.0.0.0", port=5000, threaded=True)

if __name__ == "__main__":
    try:
        start()
    except Exception:
        pass
