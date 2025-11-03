# detector.py
import cv2
import mediapipe as mp
import math
import time
from utils import save_frame_screenshot, speak_async, VolumeController

class GestureDetector:
    def __init__(self, cooldown=1.0):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False,
                                         max_num_hands=1,
                                         min_detection_confidence=0.6,
                                         min_tracking_confidence=0.6)
        self.mp_draw = mp.solutions.drawing_utils
        self.vol = VolumeController()
        self.cooldown = cooldown
        self._last_action_time = 0
        self._last_gesture = None

    # helper to detect which fingers are up (thumb,index,middle,ring,pinky)
    def _fingers_up(self, lm, w, h):
        # lm: list of landmarks (.x, .y)
        out = []
        # Thumb: compare x of tip and ip (works when frame mirrored)
        try:
            tip_x = lm[4].x * w
            ip_x = lm[3].x * w
            out.append(1 if tip_x < ip_x else 0)  # 1 if thumb pointing left in mirrored view
        except Exception:
            out.append(0)
        # Other fingers: tip.y < pip.y means finger up
        for t in (8, 12, 16, 20):
            try:
                tip_y = lm[t].y * h
                pip_y = lm[t - 2].y * h
                out.append(1 if tip_y < pip_y else 0)
            except Exception:
                out.append(0)
        return out  # [thumb, index, middle, ring, pinky]

    def _classify(self, lm, w, h):
        """Return 'thumbs_up' / 'thumbs_down' / 'peace' / None"""
        fingers = self._fingers_up(lm, w, h)
        wrist_y = lm[0].y * h
        thumb_tip_y = lm[4].y * h
        # peace: index+middle up, others down
        if fingers == [0,1,1,0,0]:
            return "peace"
        # thumbs up: thumb up (fingers closed), tip significantly above wrist
        if fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0:
            if thumb_tip_y < wrist_y - (h * 0.06):
                return "thumbs_up"
            elif thumb_tip_y > wrist_y + (h * 0.06):
                return "thumbs_down"
        return None

    def process(self, frame):
        """
        Input: BGR frame.
        Output: (frame_with_overlays, action_string_or_None)
        action_string examples: "Volume Up", "Volume Down", "Screenshot"
        """
        action = None
        now = time.time()

        h, w, _ = frame.shape
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.hands.process(img_rgb)

        if res.multi_hand_landmarks:
            hand = res.multi_hand_landmarks[0]
            # draw landmarks
            self.mp_draw.draw_landmarks(frame, hand, self.mp_hands.HAND_CONNECTIONS)
            gesture = self._classify(hand.landmark, w, h)

            # enforce cooldown and avoid repeats
            if gesture and (now - self._last_action_time > self.cooldown or gesture != self._last_gesture):
                if gesture == "thumbs_up":
                    ok = self.vol.change(0.10)
                    action = "Volume Up"
                    speak_async("Volume up")
                elif gesture == "thumbs_down":
                    ok = self.vol.change(-0.10)
                    action = "Volume Down"
                    speak_async("Volume down")
                elif gesture == "peace":
                    # take screenshot asynchronously (save_frame_screenshot expects a frame image)
                    save_frame_screenshot(frame, folder="screenshots")
                    action = "Screenshot"
                    # TTS done by save_frame_screenshot
                self._last_action_time = now
                self._last_gesture = gesture

        return frame, action
