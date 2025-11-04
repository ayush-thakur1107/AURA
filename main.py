import cv2
import time
import queue
import threading

from gestures.detector import GestureDetector
import utils as u


def voice_worker(cmd_queue):
    """Continuously listen for voice commands and enqueue them."""
    u.start_voice_listener(cmd_queue)


def handle_voice_command(cmd_text, app_state):
    """Interpret and execute recognized voice commands."""
    txt = cmd_text.lower().strip()
    print("[Voice]", txt)

    if not txt:
        return

    if "open" in txt:
        name = txt.split("open", 1)[1].strip()
        if name:
            u.open_app(name)

    elif "screenshot" in txt:
        frame = app_state.get("last_frame")
        if frame is not None:
            u.save_frame_screenshot(frame)

    elif "time" in txt:
        u.speak(f"The time is {u.get_time_str()}")

    elif "status" in txt or "system" in txt:
        u.speak(u.get_system_status())

    elif "quote" in txt or "motivate" in txt:
        u.speak(u.get_quote())

    elif "volume up" in txt:
        app_state["vol"].change(0.10)

    elif "volume down" in txt:
        app_state["vol"].change(-0.10)

    elif "remind me" in txt:
        import re
        match = re.search(r'remind me in (\d+)\s*(second|minute|hour)s?\s*to (.+)', txt)
        if match:
            num, unit, msg = int(match.group(1)), match.group(2), match.group(3)
            sec = num * (60 if "minute" in unit else (3600 if "hour" in unit else 1))
            u.set_reminder(sec, msg)
        else:
            u.speak("Sorry, I couldn't set that reminder correctly.")
    else:
        u.speak(f"I heard {txt}")


def draw_volume_bar(frame, volume_level):
    """Display volume level bar on screen."""
    h, w, _ = frame.shape
    bar_w, bar_h = 200, 12
    x, y = w - bar_w - 20, 20

    cv2.rectangle(frame, (x, y), (x + bar_w, y + bar_h), (200, 200, 200), 1)
    fill = int(bar_w * volume_level)
    cv2.rectangle(frame, (x, y), (x + fill, y + bar_h), (0, 200, 100), -1)
    cv2.putText(frame, f"VOL {int(volume_level * 100)}%", (x, y + bar_h + 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)


def main():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    time.sleep(0.4)

    if not cap.isOpened():
        print("[ERROR] Camera not accessible. Try closing other apps or use another index.")
        return

    detector = GestureDetector()
    vol_ctrl = u.VolumeController()
    cmd_queue = queue.Queue()

    threading.Thread(target=voice_worker, args=(cmd_queue,), daemon=True).start()

    app_state = {"vol": vol_ctrl, "last_frame": None}
    overlay_text = ""
    overlay_time = 0
    overlay_ttl = 2.0

    print("\n[AURA ACTIVE] Gesture + Voice assistant running. Press 'q' or 'ESC' to quit.\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)
            app_state["last_frame"] = frame

            frame, gesture, hud = detector.process(frame)

            # Gesture responses
            if gesture:
                if gesture == "thumbs_up":
                    vol_ctrl.change(0.10)
                    overlay_text = "Volume Up (gesture)"
                elif gesture == "thumbs_down":
                    vol_ctrl.change(-0.10)
                    overlay_text = "Volume Down (gesture)"
                elif gesture == "screenshot":
                    u.save_frame_screenshot(frame)
                    overlay_text = "Screenshot saved"
                overlay_time = time.time()

            # Process voice command if available
            try:
                cmd = cmd_queue.get_nowait()
                if cmd:
                    overlay_text = f"Voice: {cmd}"
                    overlay_time = time.time()
                    threading.Thread(target=handle_voice_command, args=(cmd, app_state), daemon=True).start()
            except queue.Empty:
                pass

            # Display overlay
            if overlay_text and (time.time() - overlay_time < overlay_ttl):
                cv2.putText(frame, overlay_text, (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 180), 2)

            # Display HUD info
            t = hud.get("time", "")
            sys_info = hud.get("sys", "")
            emo = hud.get("emotion", "")
            cv2.putText(frame, t, (20, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1)
            cv2.putText(frame, sys_info, (20, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            if emo:
                cv2.putText(frame, f"Emotion: {emo}", (20, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 200), 2)

            # Volume visualization
            try:
                vol_scalar = vol_ctrl._vol.GetMasterVolumeLevelScalar() if vol_ctrl._use_pycaw else 0.5
            except Exception:
                vol_scalar = 0.5
            draw_volume_bar(frame, vol_scalar)

            cv2.imshow("AURA - Live (press q to quit)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q')):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        q = getattr(u, "_speech_q", None)
        if q:
            try:
                q.put(None)
            except Exception:
                pass


if __name__ == "__main__":
    main()
