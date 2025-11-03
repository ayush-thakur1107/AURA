import os
import pyttsx3
import threading
import webbrowser
import datetime
import pyautogui
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# ---------- SPEECH ----------
def speak(text):
    """Speak text asynchronously."""
    def _speak():
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    threading.Thread(target=_speak, daemon=True).start()

# ---------- SCREENSHOT ----------
def take_screenshot():
    """Takes a screenshot and saves with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    pyautogui.screenshot(filename)
    speak("Screenshot saved.")
    return filename

# ---------- VOLUME ----------
class VolumeController:
    def __init__(self):
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))

    def set_volume(self, level):
        self.volume.SetMasterVolumeLevelScalar(level, None)

    def volume_up(self):
        current = self.volume.GetMasterVolumeLevelScalar()
        new = min(1.0, current + 0.1)
        self.volume.SetMasterVolumeLevelScalar(new, None)
        speak("Volume up.")

    def volume_down(self):
        current = self.volume.GetMasterVolumeLevelScalar()
        new = max(0.0, current - 0.1)
        self.volume.SetMasterVolumeLevelScalar(new, None)
        speak("Volume down.")

# ---------- APP / WEB CONTROL ----------
def open_app(name):
    name = name.lower()
    speak(f"Opening {name}")
    if "youtube" in name:
        webbrowser.open("https://www.youtube.com")
    elif "chrome" in name:
        os.system("start chrome")
    elif "notepad" in name:
        os.system("notepad")
    elif "explorer" in name:
        os.system("explorer")
    elif "calculator" in name:
        os.system("calc")
    elif "spotify" in name:
        os.system("start spotify")
    elif "gmail" in name:
        webbrowser.open("https://mail.google.com")
    else:
        speak("Sorry, I don't recognize that app yet.")

# ---------- COMMANDS ----------
def process_command(command):
    """Handles voice or gesture commands."""
    cmd = command.lower()
    vc = VolumeController()

    if "volume up" in cmd or "increase" in cmd:
        vc.volume_up()
    elif "volume down" in cmd or "decrease" in cmd:
        vc.volume_down()
    elif "screenshot" in cmd:
        take_screenshot()
    elif "open" in cmd:
        parts = cmd.split("open ")
        if len(parts) > 1:
            open_app(parts[1])
        else:
            speak("Open what?")
    elif "time" in cmd:
        now = datetime.datetime.now().strftime("%H:%M")
        speak(f"The time is {now}")
    else:
        speak("Command not recognized.")
