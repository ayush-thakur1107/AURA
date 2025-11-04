# gestures/detector.py
import cv2
import mediapipe as mp
import time
import numpy as np

from utils import take_screenshot_async, speak_async, VolumeController, open_app

class GestureDetector:
    def __init__(self):
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6)
        self.mp_draw = mp.solutions.drawing_utils
        self.vol = VolumeController()
        self.last_time = 0
        self.cooldown = 1.0  # seconds between actions

    def fingers_up(self, lm):
        """Return list [thumb, index, middle, ring, pinky] as 1 (up) or 0 (down)."""
        # lm: list of landmarks with .x/.y (.z ignored)
        fingers = []
        # Thumb: compare tip x to ip x (works when frame is mirrored)
        try:
            fingers.append(1 if lm[4].x < lm[3].x else 0)
        except Exception:
            fingers.append(0)
        # Other fingers: tip.y < pip.y means up
        for tip in (8, 12, 16, 20):
            try:
                fingers.append(1 if lm[tip].y < lm[tip - 2].y else 0)
            except Exception:
                fingers.append(0)
        return fingers

    def classify(self, lm, frame_h):
        """Return gesture name or None.

        Heuristics:
         - Thumbs up: thumb up (thumb tip clearly above thumb mcp/wrist) and other fingers closed
         - Thumbs down: thumb down (thumb tip clearly below wrist) and other fingers closed
         - Peace: index+middle up, others down
        """
        fingers = self.fingers_up(lm)
        # coordinates
        wrist_y = lm[0].y * frame_h
        thumb_tip_y = lm[4].y * frame_h
        thumb_ip_y = lm[3].y * frame_h

        # peace
        if fingers == [0,1,1,0,0]:
            return "peace"

        # thumbs up: thumb tip significantly above wrist and other fingers closed
        if fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0:
            if thumb_tip_y < wrist_y - frame_h * 0.06:
                return "thumbs_up"
            # side/thumb near wrist but above may be ambiguous -> ignore

        # thumbs down: thumb tip below wrist and fingers closed
        if fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0:
            if thumb_tip_y > wrist_y + frame_h * 0.06:
                return "thumbs_down"

        return None

    def process(self, frame):
        """Process frame, perform actions, return (frame, action_caption)."""
        action = None
        now = time.time()
        h, w, _ = frame.shape
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.hands.process(img_rgb)

        if res.multi_hand_landmarks:
            hand = res.multi_hand_landmarks[0]
            self.mp_draw.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)

            gesture = self.classify(hand.landmark, h)
            if gesture and (now - self.last_time) > self.cooldown:
                if gesture == "thumbs_up":
                    ok = self.vol.change_scalar(0.10)
                    speak_async("Volume up")
                    action = "Volume Up"
                elif gesture == "thumbs_down":
                    ok = self.vol.change_scalar(-0.10)
                    speak_async("Volume down")
                    action = "Volume Down"
                elif gesture == "peace":
                    # take screenshot of frame
                    take_screenshot_async(frame)
                    action = "Screenshot"
                self.last_time = now

        return frame, action
