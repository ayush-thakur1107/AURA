# main.py
import cv2
import time
import threading
import os

from gestures.detector import GestureDetector
from utils import speak_async, open_app

# Optional voice recognition (background)
try:
    import speech_recognition as sr
    HAVE_SR = True
except Exception:
    HAVE_SR = False

overlay_text = ""
overlay_time = 0
overlay_duration = 1.4

def set_overlay(text):
    global overlay_text, overlay_time
    overlay_text = text
    overlay_time = time.time()
    print("[AURA]", text)

def voice_worker():
    if not HAVE_SR:
        print("[AURA] voice not available (SpeechRecognition missing).")
        return
    r = sr.Recognizer()
    try:
        mic = sr.Microphone()
    except Exception as e:
        print("[AURA] microphone not accessible:", e)
        return

    while True:
        try:
            with mic as source:
                r.adjust_for_ambient_noise(source, duration=0.4)
                audio = r.listen(source, timeout=6, phrase_time_limit=5)
            try:
                cmd = r.recognize_google(audio).lower()
            except Exception:
                continue
            print("[voice heard]", cmd)
            set_overlay(cmd)
            if "youtube" in cmd:
                open_app("youtube")
            elif "google" in cmd:
                open_app("google")
            elif "spotify" in cmd:
                open_app("spotify")
            elif "time" in cmd:
                speak_async("The time is " + time.strftime("%I:%M %p"))
            elif "exit" in cmd or "quit" in cmd:
                speak_async("Shutting down")
                os._exit(0)
            else:
                speak_async("I heard " + cmd)
        except Exception:
            # timeouts and mic errors: loop continue
            continue

def main():
    detector = GestureDetector()
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[AURA] camera not available.")
        return

    # start voice thread
    if HAVE_SR:
        threading.Thread(target=voice_worker, daemon=True).start()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)

            frame, action = detector.process(frame)
            if action:
                set_overlay(action)

            # draw overlay
            if overlay_text and (time.time() - overlay_time < overlay_duration):
                cv2.putText(frame, overlay_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)

            # small HUD: instructions
            cv2.putText(frame, "AURA-AI", (20, frame.shape[0]-30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230,230,230), 2)

            cv2.imshow("AURA - Live", frame)
            k = cv2.waitKey(1) & 0xFF
            if k == 27 or k == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    print("[AURA] starting...")
    main()
