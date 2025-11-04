"""
detector.py
Hand gesture detector using MediaPipe (optional).
Exports GestureDetector with process(frame) -> (frame, action, hud).
If mediapipe is not installed, detector runs in no-op mode and only provides time HUD.
"""

import time
import logging
import cv2

logger = logging.getLogger("aura.detector")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# try importing mediapipe lazily
try:
    import mediapipe as mp  # type: ignore
    _HAVE_MEDIAPIPE = True
    logger.info("MediaPipe available: gesture detection enabled.")
except Exception as e:
    mp = None  # type: ignore
    _HAVE_MEDIAPIPE = False
    logger.info("MediaPipe not available: %s", e)


class GestureDetector:
    """
    Detects simple hand gestures using MediaPipe if available.
    process(frame) -> (frame, action, hud)
    action in {"thumbs_up", "thumbs_down", "screenshot"} or None
    hud: dict with keys "time", "sys", "emotion"
    """

    def __init__(self, cooldown: float = 1.0):
        self.enabled = _HAVE_MEDIAPIPE
        self.cooldown = float(cooldown)
        self._last_action_time = 0.0
        self._last_action = None
        self.hud = {"time": "", "sys": "", "emotion": ""}

        if not self.enabled:
            return

        try:
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.6,
            )
            self.mp_draw = mp.solutions.drawing_utils
        except Exception as e:
            logger.exception("Failed to initialize MediaPipe Hands: %s", e)
            self.enabled = False

    def _now_str(self) -> str:
        return time.strftime("%H:%M:%S")

    def _cooldown_ok(self) -> bool:
        return (time.time() - self._last_action_time) > self.cooldown

    def process(self, frame):
        """
        Process a BGR frame. Returns (frame, action, hud).
        Keeps frame unchanged if detection unavailable.
        """
        self.hud["time"] = self._now_str()

        if not self.enabled or frame is None:
            return frame, None, self.hud.copy()

        img = frame  # working on the same array (OpenCV drawing is in-place)
        h, w, _ = img.shape
        try:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            logger.exception("cvtColor failed: %s", e)
            return frame, None, self.hud.copy()

        try:
            res = self.hands.process(rgb)
        except Exception as e:
            logger.exception("MediaPipe processing error: %s", e)
            return frame, None, self.hud.copy()

        action = None

        if res and getattr(res, "multi_hand_landmarks", None):
            try:
                for hand_lms in res.multi_hand_landmarks:
                    # draw landmarks on the image
                    try:
                        self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
                    except Exception:
                        # drawing is non-critical
                        pass

                    # convert landmarks to pixel coordinates
                    landmarks = []
                    for lm in hand_lms.landmark:
                        landmarks.append((int(lm.x * w), int(lm.y * h)))

                    # basic finger state checks (thumb + four fingers)
                    fingers = []
                    try:
                        # thumb: compare x tip(4) and ip(3) relative to hand (works better with single handedness)
                        fingers.append(1 if landmarks[4][0] > landmarks[3][0] else 0)
                        for tip_index in (8, 12, 16, 20):
                            fingers.append(1 if landmarks[tip_index][1] < landmarks[tip_index - 2][1] else 0)
                    except Exception:
                        continue  # skip if any landmark missing

                    wrist_y = landmarks[0][1]
                    thumb_tip_y = landmarks[4][1]
                    other_fingers = fingers[1:]

                    # Thumbs up
                    if thumb_tip_y < wrist_y and other_fingers == [0, 0, 0, 0]:
                        if self._cooldown_ok():
                            action = "thumbs_up"
                    # Thumbs down
                    elif thumb_tip_y > wrist_y and other_fingers == [0, 0, 0, 0]:
                        if self._cooldown_ok():
                            action = "thumbs_down"
                    # Peace (index + middle open) -> screenshot
                    elif fingers == [0, 1, 1, 0, 0]:
                        if self._cooldown_ok():
                            action = "screenshot"

                    if action:
                        self._last_action = action
                        self._last_action_time = time.time()
                        break
            except Exception as e:
                logger.exception("Gesture parsing error: %s", e)

        return img, action, self.hud.copy()
