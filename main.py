import sys
import os
import ctypes

# Base directory: exe location (PyInstaller) or script directory
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    sys.path.insert(0, BASE_DIR)  # allow config.py override next to exe
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Single instance check via Windows mutex
_mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "whisper-hotkey-mutex")
if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    ctypes.windll.user32.MessageBoxW(0, "whisper-hotkey уже запущен", "whisper-hotkey", 0x40)
    sys.exit(0)

# Add NVIDIA DLL directories to PATH before any CUDA imports
_venv = os.path.join(BASE_DIR, ".venv", "Lib", "site-packages")
for _nv_dir in [
    os.path.join(_venv, "nvidia", "cublas", "bin"),
    os.path.join(_venv, "nvidia", "cudnn", "bin"),
]:
    if os.path.isdir(_nv_dir):
        os.environ["PATH"] = _nv_dir + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(_nv_dir)

import threading
import time
import logging
import traceback

import numpy as np
import sounddevice as sd
import keyboard
import pyperclip
import pystray
from PIL import Image, ImageDraw, ImageFont

from faster_whisper import WhisperModel
from config import (
    HOTKEY, MODEL_SIZE, DEVICE, COMPUTE_TYPE, SAMPLE_RATE, LANGUAGE,
    BEEP_START_FREQ, BEEP_START_DURATION, BEEP_STOP_FREQ, BEEP_STOP_DURATION,
)

# Logging to file next to the exe/script
LOG_PATH = os.path.join(BASE_DIR, "whisper-hotkey.log")
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("whisper-hotkey")

# Hide console window
if sys.platform == "win32":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Windows beep
try:
    import winsound
except ImportError:
    winsound = None


def _beep(freq, duration):
    if winsound:
        try:
            winsound.Beep(freq, duration)
        except Exception:
            pass


def _create_icon(color, letter="W"):
    """Create a simple tray icon with a colored circle and letter."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color)
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((64 - tw) / 2, (64 - th) / 2 - 2), letter, fill="white", font=font)
    return img


ICON_LOADING = _create_icon("#888888", "...")
ICON_READY = _create_icon("#2196F3", "W")
ICON_RECORDING = _create_icon("#F44336", "R")
ICON_PROCESSING = _create_icon("#FF9800", "...")


class VoiceTyper:
    def __init__(self):
        self.recording = False
        self.audio_frames = []
        self.stream = None
        self.model = None
        self._lock = threading.Lock()
        self.tray = None

    def _update_icon(self, icon_img, tooltip):
        if self.tray:
            self.tray.icon = icon_img
            self.tray.title = tooltip

    def load_model(self):
        self._update_icon(ICON_LOADING, "whisper-hotkey: loading model...")
        log.info(f"Loading model {MODEL_SIZE} on {DEVICE}...")

        try:
            self.model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
            log.info(f"Model loaded on {DEVICE}")
        except Exception as e:
            log.warning(f"{DEVICE} failed: {e}, falling back to CPU")
            self.model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
            log.info("Model loaded on CPU (fallback)")

        self._update_icon(ICON_READY, f"whisper-hotkey: ready ({HOTKEY})")

    def _audio_callback(self, indata, frames, time_info, status):
        if self.recording:
            self.audio_frames.append(indata.copy())

    def start_recording(self):
        if self.model is None:
            return
        with self._lock:
            if self.recording:
                return
            self.recording = True
            self.audio_frames = []

        self._update_icon(ICON_RECORDING, "whisper-hotkey: recording...")
        threading.Thread(target=_beep, args=(BEEP_START_FREQ, BEEP_START_DURATION), daemon=True).start()

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
        )
        self.stream.start()

    def stop_recording(self):
        with self._lock:
            if not self.recording:
                return
            self.recording = False
            stream = self.stream
            self.stream = None
            frames = self.audio_frames
            self.audio_frames = []

        if stream:
            stream.stop()
            stream.close()

        threading.Thread(target=_beep, args=(BEEP_STOP_FREQ, BEEP_STOP_DURATION), daemon=True).start()

        if not frames:
            self._update_icon(ICON_READY, f"whisper-hotkey: ready ({HOTKEY})")
            return

        self._update_icon(ICON_PROCESSING, "whisper-hotkey: transcribing...")
        audio = np.concatenate(frames, axis=0).flatten()
        duration = len(audio) / SAMPLE_RATE
        log.info(f"Audio recorded: {duration:.1f}s")

        try:
            t0 = time.time()
            segments, info = self.model.transcribe(
                audio,
                language=LANGUAGE,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            text = " ".join(seg.text.strip() for seg in segments).strip()
            elapsed = time.time() - t0
            log.info(f"Transcribed in {elapsed:.1f}s: {text!r}")

            if text:
                self._paste_text(text)

        except Exception as e:
            log.error(f"Transcription error: {e}\n{traceback.format_exc()}")
            self._update_icon(ICON_READY, "whisper-hotkey: ERROR (see log)")
            return

        self._update_icon(ICON_READY, f"whisper-hotkey: ready ({HOTKEY})")

    def _paste_text(self, text: str):
        old_clipboard = None
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass

        pyperclip.copy(text)
        keyboard.send("ctrl+v")

        if old_clipboard is not None:
            def restore():
                time.sleep(0.3)
                try:
                    pyperclip.copy(old_clipboard)
                except Exception:
                    pass
            threading.Thread(target=restore, daemon=True).start()

    def _setup_hotkey(self):
        keyboard.add_hotkey(HOTKEY, self._toggle, suppress=False)

    def _toggle(self):
        if self.recording:
            threading.Thread(target=self.stop_recording, daemon=True).start()
        else:
            self.start_recording()

    def _on_quit(self, icon, item):
        keyboard.unhook_all()
        icon.stop()
        os._exit(0)

    def run(self):
        menu = pystray.Menu(
            pystray.MenuItem(f"Hotkey: {HOTKEY}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit),
        )

        self.tray = pystray.Icon("whisper-hotkey", ICON_LOADING, "whisper-hotkey: starting...", menu)

        def on_tray_ready(icon):
            icon.visible = True
            self._setup_hotkey()
            self.load_model()

        threading.Thread(target=on_tray_ready, args=(self.tray,), daemon=True).start()
        self.tray.run()


if __name__ == "__main__":
    typer = VoiceTyper()
    typer.run()
