import os
import threading
import time
import webbrowser
import subprocess
import pyautogui

# TTS
try:
    import pyttsx3
    HAVE_TTS = True
except Exception:
    HAVE_TTS = False

if HAVE_TTS:
    _tts_engine = pyttsx3.init()
    _tts_engine.setProperty("rate", 170)

def speak(text: str):
    """Speak synchronously (blocking)."""
    if not HAVE_TTS:
        print("[TTS missing] " + text)
        return
    try:
        _tts_engine.say(text)
        _tts_engine.runAndWait()
    except Exception as e:
        print("[TTS error]", e)

def speak_async(text: str):
    """Speak without blocking main thread."""
    threading.Thread(target=speak, args=(text,), daemon=True).start()

# Screenshot
def _save_frame_image(frame, folder="screenshots"):
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"screenshot_{int(time.time())}.png")
    try:
        import cv2
        cv2.imwrite(filename, frame)
        speak_async("Screenshot captured")
        print("[AURA] Screenshot saved:", filename)
    except Exception as e:
        print("[AURA] Screenshot save error:", e)
        speak_async("Failed to save screenshot")

def take_screenshot_async(frame):
    """Save the passed frame asynchronously (avoid pyautogui freeze)."""
    threading.Thread(target=_save_frame_image, args=(frame.copy(),), daemon=True).start()

# App launcher
def open_app(name: str):
    name = name.lower()
    try:
        if "youtube" in name:
            webbrowser.open("https://www.youtube.com")
        elif "google" in name:
            webbrowser.open("https://www.google.com")
        elif "spotify" in name:
            subprocess.Popen("start spotify", shell=True)
        elif "vscode" in name or "code" in name:
            subprocess.Popen("code", shell=True)
        elif "notepad" in name:
            subprocess.Popen("notepad", shell=True)
        elif "calculator" in name:
            subprocess.Popen("calc", shell=True)
        else:
            speak_async(f"Can't open {name}")
            return
        speak_async(f"Opening {name}")
    except Exception as e:
        print("[open_app] error:", e)
        speak_async(f"Failed to open {name}")

# Volume Controller (pycaw primary, session fallback)
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    HAVE_PYCAW = True
except Exception:
    HAVE_PYCAW = False

class VolumeController:
    def __init__(self):
        self.volume = None
        if HAVE_PYCAW:
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            except Exception as e:
                print("[VolumeController] pycaw init failed:", e)
                self.volume = None

    def change_scalar(self, delta: float):
        """delta is relative, e.g. +0.1 or -0.1"""
        try:
            if self.volume is not None:
                cur = self.volume.GetMasterVolumeLevelScalar()
                new = min(max(cur + delta, 0.0), 1.0)
                self.volume.SetMasterVolumeLevelScalar(new, None)
                return True
            else:
                # session-level fallback
                sessions = AudioUtilities.GetAllSessions()
                for s in sessions:
                    try:
                        vol = s.SimpleAudioVolume
                        if vol is not None:
                            cur = vol.GetMasterVolume()
                            new = min(max(cur + delta, 0.0), 1.0)
                            vol.SetMasterVolume(new, None)
                    except Exception:
                        pass
                return True
        except Exception as e:
            print("[VolumeController] change error:", e)
            return False