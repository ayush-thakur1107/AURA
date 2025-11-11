

from typing import Optional
import threading
import queue
import time
import os
import webbrowser
import platform
import logging
import random

logger = logging.getLogger("aura.utils")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# ----------------- TTS (threaded queue) -----------------
_speech_q: "queue.Queue[Optional[str]]" = queue.Queue()
_have_tts = False
_tts_engine = None

try:
    import pyttsx3
    _tts_engine = pyttsx3.init()
    _tts_engine.setProperty("rate", 170)
    _have_tts = True
    logger.info("TTS engine initialized (pyttsx3).")
except Exception as e:
    logger.info("pyttsx3 not available; falling back to console prints. %s", e)
    _have_tts = False
    _tts_engine = None


def _speech_worker():
    if not _have_tts:
        # still consume queue so callers don't block on put() (not blocking here, but keep symmetry)
        while True:
            text = _speech_q.get()
            if text is None:
                break
            logger.info("[TTS disabled] %s", text)
            _speech_q.task_done()
        return

    while True:
        text = _speech_q.get()
        if text is None:
            break
        try:
            _tts_engine.say(text)
            _tts_engine.runAndWait()
        except Exception as e:
            logger.exception("TTS error: %s", e)
        _speech_q.task_done()


# start speech worker thread
threading.Thread(target=_speech_worker, daemon=True).start()


def speak(text: str) -> None:
    """Queue text for speaking (non-blocking)."""
    if not text:
        return
    try:
        _speech_q.put(text)
    except Exception:
        logger.exception("Failed to enqueue TTS; fallback print.")
        print("[TTS]", text)


# ----------------- Screenshot saver -----------------
def save_frame_screenshot(frame, folder: str = "screenshots") -> None:
    """
    Save an OpenCV BGR frame asynchronously to disk.
    frame: numpy array (BGR)
    """
    def _save(img, fpath):
        try:
            import cv2
            os.makedirs(fpath, exist_ok=True)
            name = time.strftime("screenshot_%Y%m%d_%H%M%S.png")
            path = os.path.join(fpath, name)
            cv2.imwrite(path, img)
            speak("Screenshot saved")
            logger.info("Saved screenshot: %s", path)
        except Exception as e:
            logger.exception("screenshot save error: %s", e)
            speak("Failed to save screenshot")

    try:
        threading.Thread(target=_save, args=(frame.copy(), folder), daemon=True).start()
    except Exception:
        logger.exception("Failed to start screenshot thread")


# ----------------- Volume control -----------------
class VolumeController:

    def __init__(self):
        self._use_pycaw = False
        self._vol = None
        self._pyautogui = None
        self._platform = platform.system()
        # Try pycaw on Windows
        if self._platform == "Windows":
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self._vol = cast(interface, POINTER(IAudioEndpointVolume))
                self._use_pycaw = True
                logger.info("VolumeController: using pycaw.")
            except Exception as e:
                logger.info("pycaw unavailable: %s", e)
        # Try pyautogui as fallback (works on many platforms for media keys)
        if not self._use_pycaw:
            try:
                import pyautogui
                self._pyautogui = pyautogui
                logger.info("VolumeController: using pyautogui fallback.")
            except Exception as e:
                logger.info("pyautogui unavailable: %s", e)

    def change(self, delta: float) -> bool:
        """
        delta positive raises volume, negative lowers.
        Returns True on (attempted) success, False otherwise.
        """
        try:
            if self._use_pycaw and self._vol:
                cur = self._vol.GetMasterVolumeLevelScalar()
                new = min(max(cur + delta, 0.0), 1.0)
                self._vol.SetMasterVolumeLevelScalar(new, None)
                speak(f"Volume {int(new * 100)} percent")
                return True
            elif self._pyautogui:
                steps = max(1, int(abs(delta) * 10))
                key = "volumeup" if delta > 0 else "volumedown"
                for _ in range(steps):
                    self._pyautogui.press(key)
                speak("Volume adjusted")
                return True
            else:
                logger.info("No volume control available on this system.")
        except Exception as e:
            logger.exception("change volume error: %s", e)
        return False


# ----------------- App opener -----------------
def _open_cmd(cmd: str) -> None:
    try:
        if platform.system() == "Windows":
            os.system(f"start {cmd}")
        elif platform.system() == "Darwin":
            os.system(f"open {cmd}")
        else:
            # Linux / others
            os.system(f"{cmd} &")
    except Exception as e:
        logger.exception("open command failed: %s", e)


def open_app(name: str) -> None:
    """Open a known app or search the web if unknown."""
    n = (name or "").lower()
    mapping = {
        "youtube": lambda: webbrowser.open("https://www.youtube.com"),
        "google": lambda: webbrowser.open("https://www.google.com"),
        "spotify": lambda: _open_cmd("spotify"),
        "vscode": lambda: _open_cmd("code"),
        "notepad": lambda: _open_cmd("notepad"),
        "calculator": lambda: _open_cmd("calc"),
        "chrome": lambda: _open_cmd("chrome"),
        "explorer": lambda: _open_cmd("explorer"),
    }
    for k, fn in mapping.items():
        if k in n:
            try:
                fn()
                speak(f"Opening {k}")
            except Exception as e:
                logger.exception("open_app error: %s", e)
                speak(f"Failed to open {k}")
            return
    # fallback search
    speak(f"Searching for {name}")
    webbrowser.open(f"https://www.google.com/search?q={name}")


# ----------------- System info / clock / quotes / reminders -----------------
_have_psutil = True
try:
    import psutil  # type: ignore
except Exception:
    _have_psutil = False
    logger.info("psutil not available; system info limited.")


def get_time_str() -> str:
    return time.strftime("%I:%M %p")


def get_system_status() -> str:
    try:
        if _have_psutil:
            cpu = psutil.cpu_percent(interval=0.3)
            ram = psutil.virtual_memory().percent
            try:
                battery = psutil.sensors_battery()
                bat = f"{battery.percent}%" if battery else "N/A"
            except Exception:
                bat = "N/A"
            return f"CPU {cpu}% | RAM {ram}% | BAT {bat}"
        else:
            return "System info N/A"
    except Exception as e:
        logger.exception("get_system_status error: %s", e)
        return "Sysinfo error"


_QUOTES = [
    "Discipline beats motivation every time.",
    "Small steps every day lead to big changes.",
    "Curiosity is the best teacher.",
    "You debug life by trying again.",
    "Failure is a data point for success."
]


def get_quote() -> str:
    return random.choice(_QUOTES)


def set_reminder(delay_seconds: int, text: str) -> None:
    def _job():
        time.sleep(delay_seconds)
        speak(f"Reminder: {text}")

    try:
        threading.Thread(target=_job, daemon=True).start()
        speak(f"Reminder set for {max(1, delay_seconds//60)} minutes")
    except Exception:
        logger.exception("Failed to set reminder")


# ----------------- Voice listener starter -----------------
_have_sr = True
try:
    import speech_recognition as sr  # type: ignore
except Exception:
    _have_sr = False
    logger.info("SpeechRecognition not available; voice disabled.")


def start_voice_listener(cmd_queue: "queue.Queue[str]") -> Optional[threading.Thread]:
    """
    Start background thread to listen and put recognized text into cmd_queue.
    Returns the Thread object or None if voice not available.
    """
    if not _have_sr:
        logger.info("SpeechRecognition not installed; voice disabled.")
        return None

    def _worker():
        r = sr.Recognizer()
        try:
            mic = sr.Microphone()
        except Exception as e:
            logger.exception("Microphone not accessible: %s", e)
            return
        logger.info("Voice listener started.")
        while True:
            try:
                with mic as source:
                    r.adjust_for_ambient_noise(source, duration=0.6)
                    audio = r.listen(source, timeout=6, phrase_time_limit=6)
                try:
                    txt = r.recognize_google(audio)
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    speak("Network error in speech recognition.")
                    continue
                if txt:
                    cmd_queue.put(txt)
            except Exception as e:
                # take a small pause to avoid busy-looping on repeated errors
                logger.debug("Voice listener exception: %s", e)
                time.sleep(0.2)
                continue

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
