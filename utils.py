# utilities.py
import os
import threading
import time
import webbrowser
import datetime

# TTS (pyttsx3) - init per thread to avoid blocking issues across calls
def speak_async(text: str):
    """Say `text` asynchronously (non-blocking)."""
    def _worker(txt):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.say(txt)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print("[TTS error]", e)
    threading.Thread(target=_worker, args=(text,), daemon=True).start()

# Screenshot (save a provided frame)
def save_frame_screenshot(frame, folder="screenshots"):
    """Save OpenCV frame to disk (non-blocking)."""
    def _save(img, f):
        try:
            import cv2
            os.makedirs(f, exist_ok=True)
            name = datetime.datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
            path = os.path.join(f, name)
            cv2.imwrite(path, img)
            print("[AURA] Screenshot saved:", path)
            speak_async("Screenshot saved")
        except Exception as e:
            print("[Screenshot error]", e)
            speak_async("Failed to save screenshot")
    threading.Thread(target=_save, args=(frame.copy(), folder), daemon=True).start()

# Open common apps / URLs
def open_app(name: str):
    name = name.lower()
    try:
        if "youtube" in name:
            webbrowser.open("https://www.youtube.com")
        elif "google" in name:
            webbrowser.open("https://www.google.com")
        elif "spotify" in name:
            os.system("start spotify")
        elif "vscode" in name or "code" in name:
            os.system("code")
        elif "notepad" in name:
            os.system("notepad")
        elif "calculator" in name:
            os.system("calc")
        else:
            speak_async(f"I don't have a launcher for {name}")
            return
        speak_async(f"Opening {name}")
    except Exception as e:
        print("[open_app error]", e)
        speak_async(f"Failed to open {name}")

# Volume controller (pycaw primary; pyautogui fallback)
class VolumeController:
    def __init__(self):
        self._use_pycaw = False
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._vol = cast(interface, POINTER(IAudioEndpointVolume))
            self._use_pycaw = True
        except Exception as e:
            print("[VolumeController] pycaw init failed, falling back to keypress:", e)
            self._vol = None
            # ensure pyautogui available
            try:
                import pyautogui
                self._pyautogui = pyautogui
            except Exception:
                self._pyautogui = None

    def change(self, delta_scalar: float):
        """
        Change volume by scalar delta (-1.0 .. +1.0).
        delta_scalar ~ +0.1 increases ~10%, -0.1 decreases.
        """
        try:
            if self._use_pycaw and self._vol:
                cur = self._vol.GetMasterVolumeLevelScalar()
                new = min(max(cur + delta_scalar, 0.0), 1.0)
                self._vol.SetMasterVolumeLevelScalar(new, None)
                print(f"[Volume] set {new:.2f}")
                return True
            else:
                # fallback: press OS volume keys multiple times depending on delta
                if self._pyautogui:
                    steps = int(abs(delta_scalar) * 10) or 1
                    key = "volumeup" if delta_scalar > 0 else "volumedown"
                    for _ in range(steps):
                        self._pyautogui.press(key)
                    return True
        except Exception as e:
            print("[Volume change error]", e)
        return False

# Voice command processor (simple)
def process_voice_command(cmd: str):
    """Basic mapping of voice commands to utilities."""
    if not cmd:
        return
    c = cmd.lower()
    print("[Voice Command]", c)

    # open apps
    if "youtube" in c:
        open_app("youtube")
    elif "google" in c:
        open_app("google")
    elif "spotify" in c:
        open_app("spotify")
    elif "vscode" in c or "code" in c:
        open_app("vscode")
    elif "notepad" in c:
        open_app("notepad")
    elif "screenshot" in c or "capture" in c:
        # main loop will call screenshot — here we only say intent
        speak_async("Say peace sign or I will capture.")
    elif "time" in c:
        speak_async("The time is " + time.strftime("%I:%M %p"))
    elif "exit" in c or "quit" in c or "stop" in c:
        speak_async("Shutting down Aura")
        # caller should handle shutdown if desired
    else:
        speak_async("I heard " + cmd)
