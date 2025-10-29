import cv2
import mediapipe as mp
import math
import pyautogui
import time
import threading

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,
                       min_detection_confidence=0.7,
                       min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

last_screenshot_time = 0
flash_alpha = 0  # for flash animation


def take_screenshot():
    """Capture and save screenshot in a background thread."""
    filename = f"screenshot_{int(time.time())}.png"
    pyautogui.screenshot(filename)
    print(f"🖼️ Screenshot saved as {filename}")


def recognize_gesture(frame):
    global last_screenshot_time, flash_alpha

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if not results.multi_hand_landmarks:
        return "No Hand"

    hand_landmarks = results.multi_hand_landmarks[0]
    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    landmarks = [(lm.x, lm.y) for lm in hand_landmarks.landmark]

    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]

    def distance(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    dist_thumb_index = distance(thumb_tip, index_tip)
    dist_index_middle = distance(index_tip, middle_tip)
    dist_middle_ring = distance(middle_tip, ring_tip)

    # Gesture detection
    if dist_thumb_index < 0.05:
        gesture = "Fist"
    elif dist_index_middle > 0.15 and dist_middle_ring > 0.15:
        gesture = "Peace ✌️"

        current_time = time.time()
        if current_time - last_screenshot_time > 3:
            last_screenshot_time = current_time
            threading.Thread(target=take_screenshot, daemon=True).start()
            flash_alpha = 255  # trigger flash
    else:
        gesture = "Open Palm"

    # Flash effect overlay
    if flash_alpha > 0:
        overlay = frame.copy()
        overlay[:] = (255, 255, 255)
        cv2.addWeighted(overlay, flash_alpha / 255.0, frame, 1 - (flash_alpha / 255.0), 0, frame)
        flash_alpha = max(0, flash_alpha - 25)

    return gesture
