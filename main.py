# main.py
import cv2
import time
import threading
import os

from gestures.detector import GestureDetector
from utils import speak_async, process_voice_command

# optional voice recognition
try:
    import speech_recognition as sr
    HAVE_SR = True
except Exception:
    HAVE_SR = False

overlay_text = ""
overlay_time = 0
overlay_duration = 1.6

def set_overlay(txt):
    global overlay_text, overlay_time
    overlay_text = txt
    overlay_time = time.time()
    print("[AURA]", txt)

def voice_listener_loop():
    """Background voice recognition thread. Calls utilities.process_voice_command."""
    if not HAVE_SR:
        print("[AURA] SpeechRecognition not available — voice disabled.")
        return
    r = sr.Recognizer()
    try:
        mic = sr.Microphone()
    except Exception as e:
        print("[AURA] Microphone not accessible:", e)
        return

    while True:
        try:
            with mic as source:
                r.adjust_for_ambient_noise(source, duration=0.4)
                print("[AURA] listening...")
                audio = r.listen(source, timeout=6, phrase_time_limit=5)
            try:
                cmd = r.recognize_google(audio)
            except Exception:
                continue
            set_overlay(cmd)
            # do not block UI: process command in thread
            threading.Thread(target=process_voice_command, args=(cmd,), daemon=True).start()
        except Exception:
            # timeouts / mic errors -> continue
            continue

def main():
    detector = GestureDetector()
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # prefer DirectShow on Windows
    time.sleep(0.6)  # small warm-up

    if not cap.isOpened():
        print("[AURA] Camera not available. Close other apps or try different index.")
        return

    # start voice listener
    if HAVE_SR:
        threading.Thread(target=voice_listener_loop, daemon=True).start()
    else:
        print("[AURA] Voice disabled (SpeechRecognition not installed)")

    print("[AURA] Running. q or ESC to quit.")
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                # try to recover: short sleep and continue
                time.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)  # mirror view
            frame, action = detector.process(frame)
            if action:
                set_overlay(action)

            # overlay text
            if overlay_text and (time.time() - overlay_time < overlay_duration):
                cv2.putText(frame, str(overlay_text), (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

            # helper hint
            h, w, _ = frame.shape
            cv2.putText(frame, " AURA - Press 'q' or ESC to quit ",
                        (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            # safe show
            if frame is not None and frame.size > 0:
                cv2.imshow("AURA - Live", frame)

            k = cv2.waitKey(1) & 0xFF
            if k == 27 or k == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # ensure screenshots folder exists
    os.makedirs("screenshots", exist_ok=True)
    speak_async("Aura starting")
    main()
